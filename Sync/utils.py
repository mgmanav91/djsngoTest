from Master.models import Status

def get_status(statuses, module):
    statuses = list(filter(lambda x: x , statuses))
    print("Statuses Syncing ====================")
    print(statuses)
    db_statuses = {x['name']: x['id'] \
            for x in Status.objects.filter(name__in = statuses, module=module).values("id", "name")}
    # Creating New Statuses
    new_statuses = list(set(statuses) - set(db_statuses.keys()))
    print(new_statuses)
    for i in new_statuses:
        nstatus = Status.objects.create(name=i, module="order", alias=i)
        db_statuses[i] = nstatus.id
    return db_statuses

