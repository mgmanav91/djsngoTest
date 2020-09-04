status_matrix = {'request_stock_item_confirmed': ['request_stock_item_placed', 'request_stock_item_confirmed'],
        'request_stock_item_shipped': ['request_stock_item_confirmed'],
        'request_stock_item_delivered': ['request_stock_item_shipped'],
        'request_stock_item_delivery_denied': ['request_stock_item_shipped'],
        'request_stock_item_cancelled': ['request_stock_item_placed']}
