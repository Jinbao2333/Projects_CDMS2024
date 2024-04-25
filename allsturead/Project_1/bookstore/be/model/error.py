error_code = {
    401: "Authorization failed.",
    511: "Non-existent user ID: {}",
    512: "Existing user ID: {}",
    513: "Non-existent store ID: {}",
    514: "Existing store ID: {}",
    515: "Non-existent book ID: {}",
    516: "Existing book ID: {}",
    517: "Stock level is low for book ID: {}",
    518: "Invalid order ID: {}",
    519: "Insufficient funds for order ID: {}",
    520: "Unknown error occurred.",
    521: "Unknown error occurred.",
    522: "Unknown error occurred.",
    523: "Unknown error occurred.",
    524: "Unknown error occurred.",
    525: "Unknown error occurred.",
    526: "Unknown error occurred.",
    527: "Unknown error occurred.",
    528: "Unknown error occurred."
}


def error_non_exist_user_id(user_id):
    return 511, error_code[511].format(user_id)


def error_exist_user_id(user_id):
    return 512, error_code[512].format(user_id)


def error_non_exist_store_id(store_id):
    return 513, error_code[513].format(store_id)


def error_exist_store_id(store_id):
    return 514, error_code[514].format(store_id)


def error_non_exist_book_id(book_id):
    return 515, error_code[515].format(book_id)


def error_exist_book_id(book_id):
    return 516, error_code[516].format(book_id)


def error_stock_level_low(book_id):
    return 517, error_code[517].format(book_id)


def error_invalid_order_id(order_id):
    return 518, error_code[518].format(order_id)


def error_not_sufficient_funds(order_id):
    return 519, error_code[519].format(order_id)


def error_authorization_fail():
    return 401, error_code[401]


def error_and_message(code, message):
    return code, message
