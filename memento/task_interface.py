"""
Contains MEMENTO's task interface, once the configurations are
generated and dispatched to tasks, we need some way to interact
with the user code
"""

import configurations

matrix = {}


def experiment(context, config):
    """
    Running the base experiment for all experiments

    ### Example

    ```python
    results = experiment(context, config)
    ```

    """

    def task_input(text):
        """
        Takes the experiment and sends it to the tasks
        """

        return NotImplementedError

    def task_output():
        """
        The results after the test is finished
        """

        return NotImplementedError

    def collect_metrics():
        """
        Gets the new metrics to start next experiment
        """

        return NotImplementedError

    def checkpoint():
        """
        Allows the user to revert the directory to any point in
        the past that was ‘commit’ to save the changes.
        """

        return NotImplementedError

    model = config.model()
    dataset = get_dataset(config.dataset)
    results = []
    text = context
    text_checkpoint = context.checkpoint()

    while not len(results) > 1:

        task_input(text)
        results.append(task_output())
        text = collect_metrics()
        text_checkpoint = checkpoint()

    # raise NotImplementedError

    return aggregate(results)


# memento.run(experiment, matrix)
