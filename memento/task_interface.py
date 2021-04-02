"""
Contains MEMENTO's task interface, once the configurations are
generated and dispatched to tasks, we need some way to interact
with the user code
"""


class Context:
    """
    Creates the context which interacts with the user

    ### Example

    ```python
    context_example = Context()
    context_example.collect_metrics()
    context_example.checkpoint()
    ```
    """

    def __init__(self, context=None):
        """
        Initalizes the context
        """
        self.context = context

    def collect_metrics(self):
        """
        Gets the new metrics to start next experiment
        """
        self.context.collect_metrics()
        return NotImplementedError

    def checkpoint(self):
        """
        Allows the user to revert the directory to any point in
        the past that was ‘commit’ to save the changes.
        """
        self.context.checkpoint()
        return NotImplementedError
