"""
Contains MEMENTO's task interface, once the configurations are generated and dispatched to tasks, we need some way to interact with the user code
"""
import sklearn

matrix = {
    "parameters": {
        "model": [
            sklearn.svm.SVC,
            sklearn.linear_model.Perceptron,
            sklearn.linear_model.LogisticRegression
        ],
        "dataset": ["imagenet", "mnist", "cifar10", "quickdraw"]
    }
}

def my_experiment(context, config):
    """
    Running the base experiment
    """
    model = config.model()
    dataset = get_dataset(config.dataset)
    results = []
    
    while not len(results) > 1:
        
        results.append(expensive_thing())
        context.collect_metrics()
        context.checkpoint()

    raise NotImplementedError


    return aggregate(results)



memento.run(my_experiment, matrix)
