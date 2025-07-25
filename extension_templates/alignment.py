# copyright: sktime developers, BSD-3-Clause License (see LICENSE file)
"""Extension template for unsupervised sequence aligners.

Purpose of this implementation template:
    quick implementation of new estimators following the template
    NOT a concrete class to import! This is NOT a base class or concrete class!
    This is to be used as a "fill-in" coding template.

How to use this implementation template to implement a new estimator:
- make a copy of the template in a suitable location, give it a descriptive name.
- work through all the "todo" comments below
- fill in code for mandatory methods, and optionally for optional methods
- do not write to reserved variables: is_fitted, _is_fitted, _tags, _tags_dynamic, _X
- you can add more private methods, but do not override BaseEstimator's private methods
    an easy way to be safe is to prefix your methods with "_custom"
- change docstrings for functions and the file
- ensure interface compatibility by sktime.utils.estimator_checks.check_estimator
- once complete: use as a local library, or contribute to sktime via PR
- more details:
  https://www.sktime.net/en/stable/developer_guide/add_estimators.html

Mandatory methods to implement:
    fitting                 - _fit(self, X, Z)
    get alignment           - _get_alignment(self)

Optional methods to implement:
    data conversion and capabilities tags - _tags
    get overall distance (scalar)         - _get_distance(self)
    get alignment distance matrix         - _get_distance_matrix(self)

Testing - required for sktime test framework and check_estimator usage:
    get default parameters for test instance(s) - get_test_params()

copyright: sktime developers, BSD-3-Clause License (see LICENSE file)
"""
# todo: write an informative docstring for the file or module, remove the above
# todo: add an appropriate copyright notice for your estimator
#       estimators contributed to sktime should have the copyright notice at the top
#       estimators of your own do not need to have permissive or BSD-3 copyright

# todo: uncomment the following line, enter authors' GitHub IDs
# __author__ = [authorGitHubID, anotherAuthorGitHubID]

from sktime.alignment.base import BaseAligner

# todo: add any necessary imports here

# todo: for imports of sktime soft dependencies:
# make sure to fill in the "python_dependencies" tag with the package import name
# import soft dependencies only inside methods of the class, not at the top of the file


# todo: change class name and write docstring
class MyAligner(BaseAligner):
    """Custom time series aligner. todo: write docstring.

    todo: describe your custom time series aligner here

    Parameters
    ----------
    parama : int
        descriptive explanation of parama
    paramb : string, optional (default='default')
        descriptive explanation of paramb
    paramc : boolean, optional (default=MyOtherEstimator(foo=42))
        descriptive explanation of paramc
    and so on
    """

    # optional todo: override base class estimator default tags here if necessary
    # these are the default values, only add if different to these.
    _tags = {
        # tags and full specifications are available in the tag API reference
        # https://www.sktime.net/en/stable/api_reference/tags.html
        #
        # packaging info
        # --------------
        "authors": ["author1", "author2"],  # authors, GitHub handles
        "maintainers": ["maintainer1", "maintainer2"],  # maintainers, GitHub handles
        # author = significant contribution to code at some point
        #     if interfacing a 3rd party estimator, ensure to give credit to the
        #     authors of the interfaced estimator
        # maintainer = algorithm maintainer role, "owner" of the sktime class
        #     for 3rd party interfaces, the scope is the sktime class only
        # specify one or multiple authors and maintainers, only for sktime contribution
        # remove maintainer tag if maintained by sktime core team
        #
        "python_version": None,  # PEP 440 python version specifier to limit versions
        "python_dependencies": None,  # PEP 440 python dependencies specifier,
        # e.g., "numba>0.53", or a list, e.g., ["numba>0.53", "numpy>=1.19.0"]
        # delete if no python dependencies or version limitations
        #
        # estimator tags
        # --------------
        "capability:multiple-alignment": False,  # can align more than two sequences?
        "capability:distance": False,  # does compute/return overall distance?
        "capability:distance-matrix": False,  # does compute/return distance matrix?
        "capability:unequal_length": True,  # can align sequences of unequal length?
    }

    # todo: add any hyper-parameters and components to constructor
    def __init__(self, parama, paramb="default", paramc=None):
        # estimators should precede parameters
        #  if estimators have default values, set None and initialize below

        # todo: write any hyper-parameters and components to self
        self.parama = parama
        self.paramb = paramb
        # IMPORTANT: the self.params should never be overwritten or mutated from now on
        # for handling defaults etc, write to other attributes, e.g., self._paramc
        self.paramc = paramc

        # leave this as is
        super().__init__()

        # todo: optional, parameter checking logic (if applicable) should happen here
        # if writes derived values to self, should *not* overwrite self.paramc etc
        # instead, write to self._paramc, self._newparam (starting with _)
        # example of handling conditional parameters or mutable defaults:
        if self.paramc is None:
            from sktime.somewhere import MyOtherEstimator

            self._paramc = MyOtherEstimator(foo=42)
        else:
            # estimators should be cloned to avoid side effects
            self._paramc = paramc.clone()

        # todo: if tags of estimator depend on component tags, set these here
        #  only needed if estimator is a composite
        #  tags set in the constructor apply to the object and override the class
        #
        # example 1: conditional setting of a tag
        # if est.foo == 42:
        #   self.set_tags(handles-missing-data=True)
        # example 2: cloning tags from component
        #   self.clone_tags(est2, ["enforce_index_type", "handles-missing-data"])

    # todo: implement this, mandatory
    def _fit(self, X, Z=None):
        """Fit alignment given series/sequences to align.

            core logic

        Writes to self:
            Sets fitted model attributes ending in "_".

        Parameters
        ----------
        X : list of pd.DataFrame (Series) of length n
            collection of series to align
        Z : pd.DataFrame with n rows, optional
            metadata, i-th row of Z corresponds to i-th element of X
        """

        # implement here
        # IMPORTANT: avoid side effects to X, Z
        #
        # Note: if capability:multiple-alignment is False, then n=2 always
        #  i.e., X will always be of length 2, contain only two series
        #  if capability:multiple-alignment is True, _fit needs to deal with n>=2
        #
        # Note: when interfacing a model that has fit, with parameters
        #   that are not data (X, Z) or data-like,
        #   but model parameters, *don't* add as arguments to fit, but treat as follows:
        #   1. pass to constructor,  2. write to self in constructor,
        #   3. read from self in _fit,  4. pass to interfaced_model.fit in _fit

    # todo: implement this, mandatory
    def _get_alignment(self):
        """Return alignment for sequences/series passed in fit (iloc indices).

            core logic

        Behaviour: returns an alignment for sequences in X passed to fit
            model should be in fitted state, fitted model parameters read from self

        Accesses in self:
            Fitted model attributes ending in "_".

        Returns
        -------
        pd.DataFrame in alignment format, with columns 'ind'+str(i) for integer i
            cols contain iloc index of X[i] mapped to alignment coordinate for alignment
        """

        # implement here

    # todo: consider implementing this, optional
    # if implemented, set capability:distance tag to True
    def _get_distance(self):
        """Return overall distance of alignment.

            core logic

        Behaviour: returns overall distance corresponding to alignment
            not all aligners will return or implement this (optional)
        Accesses in self:
            Fitted model attributes ending in "_".

        Returns
        -------
        distance: float - overall distance between all elements of X passed to fit
        """

        # implement here

    # todo: consider implementing this, optional
    # if implemented, set capability:distance-matrix tag to True
    def _get_distance_matrix(self):
        """Return distance matrix of alignment.

            core logic

        Behaviour: returns pairwise distance matrix of alignment distances
            not all aligners will return or implement this (optional)

        Accesses in self:
            Fitted model attributes ending in "_".

        Returns
        -------
        distmat: an (n x n) np.array of floats, where n is length of X passed to fit
            [i,j]-th entry is alignment distance between X[i] and X[j] passed to fit
        """

        # implement here

    # todo: implement this if this is an estimator contributed to sktime
    #   or to run local automated unit and integration testing of estimator
    #   method should return default parameters, so that a test instance can be created
    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.
            There are currently no reserved values for aligners.

        Returns
        -------
        params : dict or list of dict, default = {}
            Parameters to create testing instances of the class
            Each dict are parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
            `create_test_instance` uses the first (or only) dictionary in `params`
        """

        # todo: set the testing parameters for the estimators
        # Testing parameters can be dictionary or list of dictionaries.
        # Testing parameter choice should cover internal cases well.
        #   for "simple" extension, ignore the parameter_set argument.
        #
        # this method can, if required, use:
        #   class properties (e.g., inherited); parent class test case
        #   imported objects such as estimators from sktime or sklearn
        # important: all such imports should be *inside get_test_params*, not at the top
        #            since imports are used only at testing time
        #
        # A good parameter set should primarily satisfy two criteria,
        #   1. Chosen set of parameters should have a low testing time,
        #      ideally in the magnitude of few seconds for the entire test suite.
        #       This is vital for the cases where default values result in
        #       "big" models which not only increases test time but also
        #       run into the risk of test workers crashing.
        #   2. There should be a minimum two such parameter sets with different
        #      sets of values to ensure a wide range of code coverage is provided.
        #
        # example 1: specify params as dictionary
        # any number of params can be specified
        # params = {"est": value0, "parama": value1, "paramb": value2}
        #
        # example 2: specify params as list of dictionary
        # note: Only first dictionary will be used by create_test_instance
        # params = [{"est": value1, "parama": value2},
        #           {"est": value3, "parama": value4}]
        #
        # return params
