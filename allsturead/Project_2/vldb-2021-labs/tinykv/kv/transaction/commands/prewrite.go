package commands

import (
	"encoding/hex"

	"github.com/pingcap-incubator/tinykv/kv/transaction/mvcc"
	"github.com/pingcap-incubator/tinykv/proto/pkg/kvrpcpb"
	"github.com/pingcap/log"
	"go.uber.org/zap"
)

// Prewrite represents the prewrite stage of a transaction. A prewrite contains all writes (but not reads) in a transaction,
// if the whole transaction can be written to underlying storage atomically and without conflicting with other
// transactions (complete or in-progress) then success is returned to the client. If all a client's prewrites succeed,
// then it will send a commit message. I.e., prewrite is the first phase in a two phase commit.
type Prewrite struct {
	CommandBase
	request *kvrpcpb.PrewriteRequest
}

func NewPrewrite(request *kvrpcpb.PrewriteRequest) Prewrite {
	return Prewrite{
		CommandBase: CommandBase{
			context: request.Context,
			startTs: request.StartVersion,
		},
		request: request,
	}
}

// PrepareWrites prepares the data to be written to the raftstore. The data flow is as follows.
// The tinysql part:
// 		user client -> insert/delete query -> tinysql server
//      query -> parser -> planner -> executor -> the transaction memory buffer
//		memory buffer -> kv muations -> kv client 2pc committer
//		committer -> prewrite all the keys
//		committer -> commit all the keys
//		tinysql server -> respond to the user client
// The tinykv part:
//		prewrite requests -> transaction mutations -> raft request
//		raft req -> raft router -> raft worker -> peer propose raft req
//		raft worker -> peer receive majority response for the propose raft req  -> peer raft committed entries
//  	raft worker -> process committed entries -> send apply req to apply worker
//		apply worker -> apply the correspond requests to storage(the state machine) -> callback
//		callback -> signal the response action -> response to kv client
func (p *Prewrite) PrepareWrites(txn *mvcc.MvccTxn) (interface{}, error) {
	response := new(kvrpcpb.PrewriteResponse)

	// Prewrite all mutations in the request.
	for _, m := range p.request.Mutations {
		keyError, err := p.prewriteMutation(txn, m)
		if keyError != nil {
			response.Errors = append(response.Errors, keyError)
		} else if err != nil {
			return nil, err
		}
	}

	return response, nil
}

// prewriteMutation prewrites mut to txn. It returns (nil, nil) on success, (err, nil) if the key in mut is already
// locked or there is any other key error, and (nil, err) if an internal error occurs.
func (p *Prewrite) prewriteMutation(txn *mvcc.MvccTxn, mut *kvrpcpb.Mutation) (*kvrpcpb.KeyError, error) {
	key := mut.Key
	log.Debug("prewrite key", zap.Uint64("start_ts", txn.StartTS),
		zap.String("key", hex.EncodeToString(key)))

	// DONE
	// YOUR CODE HERE (lab2).
	// Check for write conflicts.
	// Hint: Check the interafaces provided by `mvcc.MvccTxn`. The error type `kvrpcpb.WriteConflict` is used
	//		 denote to write conflict error, try to set error information properly in the `kvrpcpb.KeyError`
	//		 response.
	_, commitTs, err := txn.MostRecentWrite(key)
	if err != nil {
		return nil, err
	}
	if commitTs > txn.StartTS {
		return &kvrpcpb.KeyError{Conflict: &kvrpcpb.WriteConflict{
			StartTs:    txn.StartTS,
			ConflictTs: commitTs,
			Key:        key,
			Primary:    p.request.PrimaryLock,
		}}, nil
	}

	// DONE
	// YOUR CODE HERE (lab2).
	// Check if key is locked. Report key is locked error if lock does exist, note the key could be locked
	// by this transaction already and the current prewrite request is stale.
	lock, err := txn.GetLock(key)
	if err != nil {
		return nil, err
	}
	if lock != nil && lock.Ts != txn.StartTS {
		return &kvrpcpb.KeyError{Locked: lock.Info(key)}, nil
	}

	// DONE
	// YOUR CODE HERE (lab2).
	// Write a lock and value.
	// Hint: Check the interfaces provided by `mvccTxn.Txn`.
	var writeKind mvcc.WriteKind
	switch mut.Op {
	case kvrpcpb.Op_Put:
		writeKind = mvcc.WriteKindPut
		txn.PutValue(key, mut.Value)
	case kvrpcpb.Op_Del:
		writeKind = mvcc.WriteKindDelete
		txn.DeleteValue(key)
	}
	lock = &mvcc.Lock{
		Primary: p.request.PrimaryLock,
		Ts:      txn.StartTS,
		Kind:    writeKind,
	}
	txn.PutLock(key, lock)

	return nil, nil
}

func (p *Prewrite) WillWrite() [][]byte {
	result := [][]byte{}
	for _, m := range p.request.Mutations {
		result = append(result, m.Key)
	}
	return result
}
