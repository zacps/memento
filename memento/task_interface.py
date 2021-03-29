"""
Contains MEMENTO's task interface, once the configurations are
generated and dispatched to tasks, we need some way to interact
with the user code
"""

#import configurations
#import parallel

matrix = {}


def experiment(context, config):
    """
    Running the base experiment for all experiments

    ### Example

    ```python
    results = experiment(context, config)
    ```

    """

    def task_input(text, model, dataset):
        """
        Takes the experiment and sends it to the tasks
        """

        return NotImplementedError

    def task_output():
        """
        The results after the test is finished
        """

        return NotImplementedError

    def get_dataset(config):
        """
        Gets the data set from configurations
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

    def aggregate(list_of_results):
        """
        Combines all the results
        """

        return NotImplementedError

    model = config.model()
    dataset = get_dataset(config.dataset)
    results = []
    text = context
    checkpoint()

    while len(results) <= 1:

        task_input(text, model, dataset)
        results.append(task_output())
        text = collect_metrics()
        checkpoint()

    # raise NotImplementedError

    return aggregate(results)


# memento.run(experiment, matrix)
