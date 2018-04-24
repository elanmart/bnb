# What's in this repo?

See my blog post on [staying sane while doing ML](https://elanmart.github.io/2018-02-02-staying-sane)
for a brief description of how I handle my machine learning experiments.

This repo contains code that I use for this exact purpose.

It is not intended to be package that you can install and use reliably. 
This is a personal project, but I'll be happy if you find at least part
of it usefull.

# Docs / Examples

There is currently no docs, but see the [blog post](https://elanmart.github.io/2018-02-02-staying-sane) 
for philosophy, and [example notebook](https://github.com/elanmart/bnb/blob/master/examples/bnb-vis.ipynb) for some usage example.

# Note

* You'll probably be much better of by using [sacred](https://github.com/IDSIA/sacred).

* This code needs a major refactor -- it was cut out from a larger project
that was also handling job scheduling for my AWS workers (see [this repo](https://github.com/elanmart/bnb-full)). It therefore contains a lot of code that could be greatly 
simplified

# Summary

I use `bnb` to track my ML experiments. 

```python
from sklearn import datasets, ensemble, metrics
from bnb import Experiment, get_current_context

ex = Experiment('iris', 'mytag', dirty_ok=True, auto_enabled=True)

@ex.watch
def main(n_estimators, max_depth, criterion):
    ctx = get_current_context()
    clf = ensemble.RandomForestClassifier(n_estimators=n_estimators,
                                          max_depth=max_depth,
                                          criterion=criterion)

    iris = datasets.load_iris()
    X, y = iris.data, iris.target
    clf = clf.fit(X, y)
    p = clf.predict(X)

    precision = metrics.precision_score(y, p, average='macro')
    recall = metrics.recall_score(y, p, average='macro')
    
    ctx.report('precision', precision)
    ctx.report('recall', recall)   
```

Running experiments like in the snippet below will create entries in a `TinyDB` database that can be later conveniently explored

Experiment:
```python
for ne in [-1, 1, 2, 3, 4]:
    for md in [-1, 1, 2, 3, 4]:
        main(ne, md, criterion='gini')
```

Getting top 3 best runs, showing only the scores and config
```python
>>> from bnb.vis.core import get
>>> res = get('iris')
>>> res.top_k(('precision', 'recall'), k=3).no_details().df
     results              config                       
   precision    recall criterion max_depth n_estimators
19  0.993464  0.993333      gini         4            3
24  0.980125  0.980000      gini         4            4
9   0.975309  0.973333      gini         4            1

>>> res.top_k(('precision', 'recall'), k=3).no_details().compare().df
     results                 config
   precision    recall n_estimators
19  0.993464  0.993333            3
24  0.980125  0.980000            4
9   0.975309  0.973333            1
```
