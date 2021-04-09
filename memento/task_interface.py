"""
Contains MEMENTO's task interface, once the configurations are
generated and dispatched to tasks, we need some way to interact
with the user code
"""

from memento.configurations import run


class Context:
    """
    Creates the context which interacts with the user

    ### Example

    ```python
    context_example = Context()
    context_example.results(tasks)
    context_example.collect_metrics()
    context_example.checkpoint()
    context_example.restore(2)
    ```
    """

    def __init__(self, context=None):
        """
        Initalizes the context
        """
        self.context = context
        self.results(run(context))

    def results(self, task):
        """
        return class from Memento.run which wild hold
        the results of the tasks themselves and any metadata we
        want to add
        """
        self.task = task
        self.task_results = self.task.result()
        self.metadata = self.task.metadata()

    def collect_metrics(self):
        """
        Gets the new metrics to start next experiment
        """
        return self.collect_metrics()

    def checkpoint(self):
        """
        Allows the user to revert the directory to any point in
        the past that was ‘commit’ to save the changes.
        """
        return self.checkpoint()

    def restore(self, checkpoint):
        """
        Gets the data saved at the checkpoint the user want to retrieve
        from
        """
        return self.restore(checkpoint)
