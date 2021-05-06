def my_experiment():
    data1 = context.checkpoint(expensive_thing_1)(1)

    if checkpoint_exists(2):
        data2 = restore_checkpoint(2)
    else:
        data2 = do_expensive_thing2(data1)
        checkpoint(data2)

    if checkpoint_exists(3):
        data2 = restore_checkpoint(3)
    else:
        data2 = do_expensive_thing3(data2)
        checkpoint(data3)