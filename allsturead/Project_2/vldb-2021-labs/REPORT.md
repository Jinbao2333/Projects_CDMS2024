# VLDB Lab 2021
## Lab 1

Lab 1 介绍了分布式事务型数据库系统的设计，这里着眼于存储和日志层。该系统旨在确保事务系统的 ACID 特性，尤其是持久性（Durability），通过在分布式环境中改进日志的可用性（Availability）和可靠性（Reliability）来实现。这主要依靠将事务日志复制到多个节点，从而降低日志丢失的可能性。

为了实现这一目标，该项目采用了 `Raft` 算法来复制日志。Raft 被用作共识算法，确保日志在不同副本节点之间的一致性。只有当大多数副本节点接受并成功复制日志后，日志才被认为是提交的（committed），这确保了事务的持久性。

接下来，我们根据实验指导文档，逐步来看 Lab 1 的任务。

### P0

P0 部分的主要任务就是补全 `standalone_storage.go` 部分的代码，以下是我们具体的实现和介绍。

`standalone_storage.go`: 
- `Reader`: 接受一个 `*kvrpcpb.Context` 类型的参数，表示一个 KV RPC 的上下文。这个方法的主要作用是创建一个 `StorageReader`，用于从存储中读取数据。在方法体中，首先调用 `s.db.NewTransaction(false)` 创建一个新的只读事务，然后将这个事务传递给 `NewBadgerReader` 函数，创建一个 `BadgerReader` 实例。`BadgerReader` 结构体是 `StorageReader` 接口的一个实现，用于从 Badger 数据库中读取数据。
- `Write`: `Write` 方法的主要作用是将一批修改操作（由 `[]storage.Modify` 类型的参数 `batch` 表示）写入到存储中。每个 `storage.Modify` 对象包含一个 `Data` 字段，该字段可以是 `storage.Put` 或 `storage.Delete` 类型，分别表示插入/更新操作和删除操作。
    
    在方法体中，首先遍历 `batch` 参数中的所有修改操作。对于每一个修改操作，使用类型断言检查其 `Data` 字段的实际类型。

    如果 `Data` 字段的类型是 `storage.Put`，即一个插入或更新操作。在这种情况下，我们将 `Data` 字段转换为 `storage.Put` 类型，然后调用 `engine_util.PutCF` 函数将数据写入到数据库中。`PutCF` 函数接受四个参数：数据库实例、列族名称、键和值。如果写入操作失败，返回错误。

    而如果 `Data` 字段的类型是 `storage.Delete`，则表示这是一个删除操作。在这种情况下，我们将 `Data` 字段转换为 `storage.Delete` 类型，然后调用 `engine_util.DeleteCF` 函数将数据从数据库中删除。`DeleteCF` 函数接受三个参数：数据库实例、列族名称和键。如果删除操作失败，返回错误。

    需要注意的是，指导文件中已经指出了 Badger 数据库不支持列族（Column Family），所以这里使用了一个包装器来模拟列族的功能。这是通过 `engine_util.PutCF` 和 `engine_util.DeleteCF` 函数实现的，这两个函数都接受列族名称作为参数，并在内部将列族名称和键组合成新的键，然后对这个新的键进行操作。

完成以后，我们对这部分进行评测（开始时遇到了错误，见后文的错误记录 1 ），通过了这部分的评测，具体地，得到如下输出结果。

```bash
jinbao@JinbaosLaptop:/mnt/d/Projects_CDMS2024/allsturead/Project_2/vldb-2021-labs/tinykv$ make lab1P0
GO111MODULE=on go test -v --count=1 --parallel=1 -p=1 ./kv/server -run 1
=== RUN   TestRawGet1
--- PASS: TestRawGet1 (0.77s)
=== RUN   TestRawGetNotFound1
--- PASS: TestRawGetNotFound1 (0.65s)
=== RUN   TestRawPut1
--- PASS: TestRawPut1 (0.74s)
=== RUN   TestRawGetAfterRawPut1
--- PASS: TestRawGetAfterRawPut1 (0.80s)
=== RUN   TestRawGetAfterRawDelete1
--- PASS: TestRawGetAfterRawDelete1 (1.12s)
=== RUN   TestRawDelete1
--- PASS: TestRawDelete1 (1.10s)
=== RUN   TestRawScan1
--- PASS: TestRawScan1 (0.80s)
=== RUN   TestRawScanAfterRawPut1
--- PASS: TestRawScanAfterRawPut1 (1.13s)
=== RUN   TestRawScanAfterRawDelete1
--- PASS: TestRawScanAfterRawDelete1 (0.94s)
=== RUN   TestIterWithRawDelete1
--- PASS: TestIterWithRawDelete1 (0.51s)
PASS
ok      github.com/pingcap-incubator/tinykv/kv/server   8.569s
```

### P1

Lab 1 中剩余的 P1 工作主要集中在实现`kv/raftstore`目录下的几个关键方法，这些方法主要用于确保 Raft 协议的正常运作、日志的持久化以及状态机的更新。

#### 任务总览

1. **实现提议Raft命令**：
   - 在 `kv/raftstore/peer_msg_handler.go` 中，需要完成 `proposeRaftCommand` 方法的编码工作。这个方法是处理读写请求提案的核心，负责将客户端的读写请求转化为 Raft 协议可处理的命令形式，以便进行共识和日志复制。

2. **处理Raft就绪状态**：
   - 在 `kv/raftstore/peer.go` 中，需要实现 `HandleRaftReady` 方法。这个方法负责处理 Raft 实例返回的 Ready 状态，包括发送消息给其他节点、持久化 Raft 状态和日志等关键步骤，是 Raft 状态机推进的核心逻辑。

3. **保存就绪状态**：
   - 在 `kv/raftstore/peer_storage.go` 中，首先需要实现 `SaveReadyState` 方法。此方法专注于持久化 Raft 的当前状态和相关日志，确保即使在节点故障的情况下也能恢复到最新的状态，是实现持久化和故障恢复能力的关键环节。

4. **追加Raft日志到日志引擎**：
   - 在 `kv/raftstore/peer_storage.go`中，需要完成 `Append` 方法的实现。这个方法负责将 Raft Ready 中的日志条目追加到日志引擎中，是日志复制和持久化过程的直接执行者，确保数据的一致性和持久性。

以下是具体实施和方法介绍。

#### `kv/raftstore/peer_msg_handler.go`: 

`peerMsgHandler` 结构体的 `proposeRaftCommand` 方法接受两个参数：一个 `*raft_cmdpb.RaftCmdRequest` 类型的参数，表示一个 Raft 命令请求，和一个 `*message.Callback` 类型的参数，表示一个回调函数。

在注释中，我们可以得到实现这个方法的一些提示：

1. 首先，需要对命令进行 `preProposeRaftCommand` 检查。如果检查失败，需要执行回调函数，并返回错误结果。可以使用 `ErrResp` 来生成错误响应。

2. 然后，需要检查 peer 是否已经停止。如果已经停止，需要通知回调函数该 region 已被移除。可以查看 `destroy` 函数以获取相关的实用程序。可以使用 `NotifyReqRegionRemoved` 来生成错误响应。

3. 最后，需要将可能的响应与 term 绑定，然后使用 `Propose` 函数进行实际的请求提议。

需要注意的是，正在检查的 peer 可能是一个 leader，但它可能会在后面变为 follower。无论 peer 是否为 leader 都没有关系。如果它不是 leader，那么提议的命令日志条目就不能被提交。在 `peerMsgHandler` 的 `ctx` 中有一些参考信息。

下面是这部分的补全代码实现。

```go
func (d *peerMsgHandler) proposeRaftCommand(msg *raft_cmdpb.RaftCmdRequest, cb *message.Callback) {
        panic("not implemented yet")
        // YOUR CODE HERE (lab1).
        // Hint1: do `preProposeRaftCommand` check for the command, if the check fails, need to execute the
        // callback function and return the error results. `ErrResp` is useful to generate error response.
        if err := d.preProposeRaftCommand(msg); err != nil {
            cb.Done(ErrResp(err))
            return
        }
        // Hint2: Check if peer is stopped already, if so notify the callback that the region is removed, check
        // the `destroy` function for related utilities. `NotifyReqRegionRemoved` is useful to generate error response.
        if d.peer.stopped {
            cb.Done(ErrResp(NotifyReqRegionRemoved()))
        }
        // Hint3: Bind the possible response with term then do the real requests propose using the `Propose` function.
        // Note:
        // The peer that is being checked is a leader. It might step down to be a follower later. It
        // doesn't matter whether the peer is a leader or not. If it's not a leader, the proposing
        // command log entry can't be committed. There are some useful information in the `ctx` of the `peerMsgHandler`.
        resp := &raft_cmdpb.RaftCmdResponse{}
        BindRespTerm(resp, d.peer.Term())
        ctx := d.ctx
        d.peer.Propose(ctx.engine.Kv, ctx.cfg, cb, msg, resp)
    }
```

#### `kv/raftstore/peer.go`: 
函数 `HandleRaftReady` 是处理 Raft 协议中的 "ready" 状态的方法。"ready" 状态表示 Raft 节点已经准备好进行一些操作，例如发送消息、应用日志条目或者应用快照。

函数的主要步骤：

1. 检查 peer 是否已经停止，或者是否有待处理的快照但还未准备好处理，如果是，则直接返回。

2. 开始处理 Raft 的 "ready" 状态。如果 "ready" 状态中有快照，但是快照的元数据为空，那么会创建一个新的元数据。

3. 如果当前 peer 是 leader，那么会发送 "ready" 状态中的所有消息，并清空这些消息。

4. 如果 "ready" 状态的软状态（SoftState）存在，并且 Raft 状态是 leader，那么会调度一个心跳任务。

5. 尝试保存 "ready" 状态。如果保存失败，函数会 panic。如果当前 peer 不是 leader，那么会发送 "ready" 状态中的所有消息。

6. 如果应用了快照，那么会将当前 peer 注册到消息中，以便后续使用。同时，更新 LastApplyingIdx 为快照的元数据中的索引。如果没有应用快照，那么会处理 "ready" 状态中已提交的日志条目。如果有已提交的日志条目，那么会更新 LastApplyingIdx 为最后一个日志条目的索引，并将这些日志条目添加到消息中。

函数最后返回应用快照的结果和消息。

根据注释的提示，**需要补全的代码**部分主要有两个：

1. 在开始处理 Raft 的 "ready" 状态之前，需要检查是否有 "ready" 状态需要处理，如果没有，则直接返回。代码如下。
        ```go
        if !p.RaftGroup.HasReady() {
            return nil, msgs
        }
        ```

2. 在处理完 "ready" 状态后，需要尝试推进 Raft 组的状态。这需要通过调用 Raft 组的 `Advance` 方法来完成。
        ```go
        p.RaftGroup.Advance(ready)
        ```

#### `kv/raftstore/peer_storage.go`:
    
##### `SaveReadyState`: 

首先，检查 "ready" 状态中的日志条目是否为空。如果不为空，那么就调用 `ps.Append(ready.Entries, raftWB)` 方法处理这些日志条目。这个方法会将日志条目追加到 Raft 的写入批次中；然后检查 `ps.raftState.LastIndex` 是否大于 0。如果大于 0，那么表示这个 peer 不是刚从 Raft 消息创建的，已经应用过快照，所以需要处理硬状态。接着，检查 "ready" 状态中的硬状态是否为空。如果不为空，那么就将其保存到 `ps.raftState.HardState` 中。这段代码根据 "ready" 状态的内容，更新 peer 的状态，确保 Raft 集群的状态一致。

##### `Append`: 

第一个循环中，首先我们生成一个日志键 `log_key`，其中 `ps.region.GetId()` 是 region 的 ID，`entry.Index` 是日志条目的索引；该日志键用于在 Raft 的写入批次中标识这个日志条目。然后将日志条目作为元数据类型的键值对保存到 Raft 的写入批次中。第二个循环的目的类似，只是进行删除日志条目。在这个过程中，首先还是生成一个日志键，然后删除 Raft 的写入批次中对应的日志条目。这是在处理旧的、可能与新的日志条目冲突的日志条目时使用的。

完成以上部分后，我们对 P1 部分进行评测。根据指导文档，我们可以知道不同的命令可以进行不同侧重的评测，从而针对性地修改优化代码。具体 `make` 命令以及评测内容如下。
- `make lab1P1a`：关于 `raftStore` 逻辑的基本测试。
- `make lab1P1b` ：也是关于 `raftStore` 逻辑的基本测试，但是在测试过程中会注入一些故障，以测试 `raftStore` 在面对故障时的行为。
- `make lab1P2a`：关于 `raftStore` 的持久性测试，主要检查 `raftStore` 是否能正确地保存和恢复状态。
- `make lab1P2b` ：同上，增加故障注入。
- `make lab1P3a`：关于 `raftStore` 的快照相关测试，主要检查 `raftStore` 是否能正确地创建和应用快照。
- `make lab1P3b` ：同上，增加故障注入。
- `make lab1P4a`：这是关于 `raftStore` 的配置更改测试，主要检查 `raftStore` 是否能正确地处理配置更改。
- `make lab1P4b` ：同上，增加故障注入。

可以看到，这些 a 部分的测试覆盖了 `raftStore` 的主要功能，并在此基础通过 b 部分的故障注入来测试其鲁棒性。

经过漫长的运行之后，我们通过了所有八项测试，这也宣告了我们对 Lab 1 全部工作的完成。由于测试输出结果较长，我们就不在此展示具体输出结果了。

## Lab 2



## 错误记录
1. 当我们第一次在本地进行 `make lab1P0` ，进行第一部分的评分时，出现了一些错误，报错信息如下。
    ```bash
    jinbao@JinbaosLaptop:/mnt/d/Projects_CDMS2024/allsturead/Project_2/vldb-2021-labs/tinykv$ make lab1P0
    GO111MODULE=on go test -v --count=1 --parallel=1 -p=1 ./kv/server -run 1
    go: github.com/BurntSushi/toml@v0.3.1: Get "https://proxy.golang.org/github.com/%21burnt%21sushi/toml/@v/v0.3.1.mod": dial tcp: lookup proxy.golang.org on 10.255.255.254:53: server misbehaving
    go: downloading github.com/pingcap/errors v0.11.5-0.20190809092503-95897b64e011
    go: downloading github.com/pingcap/log v0.0.0-20200117041106-d28c14d3b1cd
    go: downloading github.com/pingcap-incubator/tinysql v0.0.0-20200518090433-a7d00f9e6aa7
    go: downloading github.com/stretchr/testify v1.4.0
    go: downloading github.com/gogo/protobuf v1.3.1
    go: downloading github.com/golang/protobuf v1.3.4
    go: downloading golang.org/x/net v0.0.0-20200226121028-0de0cce0169b
    go: downloading google.golang.org/grpc v1.25.1
    go: downloading github.com/Connor1996/badger v1.5.1-0.20211220080806-e856748bd047
    go: downloading github.com/petar/GoLLRB v0.0.0-20190514000832-33fb24c13b99
    go: downloading github.com/juju/errors v0.0.0-20181118221551-089d3ea4e4d5
    go: downloading github.com/pingcap/tipb v0.0.0-20200212061130-c4d518eb1d60
    go: downloading go.uber.org/zap v1.14.0
    go: downloading github.com/coreos/pkg v0.0.0-20180928190104-399ea9e2e55f
    go: downloading github.com/pkg/errors v0.8.1
    go: downloading github.com/sirupsen/logrus v1.2.0
    go: downloading go.etcd.io/etcd v0.5.0-alpha.5.0.20191023171146-3cf2f69b5738
    go: downloading gopkg.in/natefinch/lumberjack.v2 v2.0.0
    go: downloading github.com/shirou/gopsutil v2.19.10+incompatible
    go: github.com/BurntSushi/toml@v0.3.1: Get "https://proxy.golang.org/github.com/%21burnt%21sushi/toml/@v/v0.3.1.mod": dial tcp: lookup proxy.golang.org on 10.255.255.254:53: server misbehaving
    make: *** [Makefile:109: lab1P0] Error 1
    ```

    查阅资料得知，遇到的问题是 Go 语言的模块代理（Go module proxy）无法访问。错误信息中的 `dial tcp: lookup proxy.golang.org on 10.255.255.254:53: server misbehaving` 表示在尝试访问 `proxy.golang.org` 时出现了问题。通过查阅资料得知这可能是由于网络问题，或者是因为环境中的 DNS 设置问题。

    此后查阅指导文档，尝试进行命令 `export GOPROXY=https://goproxy.io,direct` 将 Go 语言的模块代理服务器设置为 `https://goproxy.io`，当其无法使用时直接从源服务器获取依赖，便可以成功运行测试脚本了。
