from suit.apps import DjangoSuitConfig
from suit.menu import ParentItem, ChildItem

class SuitConfig(DjangoSuitConfig):
    menu = (
            ParentItem('Setup', children=[
                ChildItem(model='Master.location'),
                ChildItem(model='Master.status'),
                ChildItem(model='Master.txntype'),
                ChildItem(model='Master.tax'),
                ], icon='fa fa-wrench'),
            ParentItem('Master Item', children=[
                ChildItem(model='Master.barcodes'),
                ChildItem(model='Master.brands'),
                ChildItem(model='Master.category'),
                ChildItem(model='Master.product'),
                ChildItem(model='Master.productdefaultprice'),
                ], icon='fa fa-th-list'),
            ParentItem('Store Master', children=[
                ChildItem(model='Store.store'),
                ChildItem(model='Store.storecustomproduct'),
                ChildItem(model='Store.storeinventory'),
                ], icon='fa fa-building'),
            ParentItem('Orders', children=[
                ChildItem(model='Store.storesale'),
                ChildItem(model='Store.storecustomer'),
                ], icon='fa fa-credit-card'),
            ParentItem('Stocks', children=[
                ChildItem(model='Stocks.stockrequest'),
                ChildItem(model='Stocks.stockrequestitem'),
                ChildItem(model='Stocks.packagedispatcher'),
                ], icon='fa fa-reorder'),
	)
    layout = 'vertical'
