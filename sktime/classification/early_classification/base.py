# copyright: sktime developers, BSD-3-Clause License (see LICENSE file)
"""Abstract base class for early time series classifiers.

    class name: BaseEarlyClassifier

Defining methods:
    fitting                 - fit(self, X, y)
    predicting              - predict(self, X)
                            - predict_proba(self, X)
    updating predictions    - update_predict(self, X)
      (streaming)           - update_predict_proba(self, X)

Inherited inspection methods:
    hyper-parameter inspection  - get_params()
    fitted parameter inspection - get_fitted_params()

State:
    fitted model/strategy   - by convention, any attributes ending in "_"
    fitted state flag       - is_fitted (property)
    fitted state inspection - check_is_fitted()
    streaming decision info - state_info attribute
"""

__all__ = [
    "BaseEarlyClassifier",
]
__author__ = ["mloning", "fkiraly", "TonyBagnall", "MatthewMiddlehurst"]

from abc import abstractmethod

import numpy as np

from sktime.base import BaseEstimator
from sktime.classification import BaseClassifier


class BaseEarlyClassifier(BaseEstimator):
    """Abstract base class for early time series classifiers.

    The base classifier specifies the methods and method signatures that all
    early classifiers have to implement. Attributes with an underscore suffix are set in
    the method fit.

    Parameters
    ----------
    classes_            : ndarray of class labels, possibly strings
    n_classes_          : integer, number of classes (length of classes_)
    fit_time_           : integer, time (in milliseconds) for fit to run.
    _class_dictionary   : dictionary mapping classes_ onto integers 0...n_classes_-1.
    _threads_to_use     : number of threads to use in fit as determined by n_jobs.
    state_info          : An array containing the state info for each decision in X.
    """

    _tags = {
        "object_type": "early_classifier",  # type of object
        "X_inner_mtype": "numpy3D",  # which type do _fit/_predict, support for X?
        "y_inner_mtype": "numpy1D",  # which type do _fit/_predict, support for y?
        #    it should be either "numpy3D" or "nested_univ" (nested pd.DataFrame)
        "capability:multioutput": False,  # whether classifier supports multioutput
        "capability:multivariate": False,
        "capability:unequal_length": False,
        "capability:missing_values": False,
        "capability:multithreading": False,
    }

    # convenience constant to control which metadata of input data
    # are regularly retrieved in input checks
    METADATA_REQ_IN_CHECKS = [
        "n_instances",
        "has_nans",
        "is_univariate",
        "is_equal_length",
        "feature_kind",
    ]

    # attribute name where vectorized estimators are stored
    VECTORIZATION_ATTR = "classifiers_"  # e.g., classifiers_, regressors_

    # used in error messages
    TASK = "early classification"  # e.g., classification, regression
    EST_TYPE = "early classifier"  # e.g., classifier, regressor
    EST_TYPE_PLURAL = "early classifiers"  # e.g., classifiers, regressors

    def __init__(self):
        self.classes_ = []
        self.n_classes_ = 0
        self.fit_time_ = 0
        self._class_dictionary = {}
        """An array containing the state info for each decision in X from update and
        predict methods.

        Contains classifier dependent information for future decisions on the data and
        information on when a cases decision has been made. Each row contains
        information for a case from the latest decision on its safety made in
        update/predict. Successive updates are likely to remove rows from the
        state_info, as it will only store as many rows as there are input instances to
        update/predict.
        """
        self.state_info = None

        self._converter_store_y = {}

        super().__init__()

    def fit(self, X, y):
        """Fit time series classifier to training data.

        Parameters
        ----------
        X : 3D np.array (any number of dimensions, equal length series)
                of shape [n_instances, n_dimensions, series_length]
            or 2D np.array (univariate, equal length series)
                of shape [n_instances, series_length]
            or pd.DataFrame with each column a dimension, each cell a pd.Series
                (any number of dimensions, equal or unequal length series)
            or of any other supported Panel mtype
                for list of mtypes, see datatypes.SCITYPE_REGISTER
                for specifications, see examples/AA_datatypes_and_datasets.ipynb
        y : 1D np.array of int, of shape [n_instances] - class labels for fitting
            indices correspond to instance indices in X

        Returns
        -------
        self : Reference to self.

        Notes
        -----
        Changes state by creating a fitted model that updates attributes
        ending in "_" and sets is_fitted flag to True.
        """
        fit = BaseClassifier.fit
        return fit(self, X, y)

    def predict(self, X) -> tuple[np.ndarray, np.ndarray]:
        """Predicts labels for sequences in X.

        Early classifiers can predict at series lengths shorter than the train data
        series length.

        Predict will return -1 for cases which it cannot make a decision on yet. The
        output is only guaranteed to return a valid class label for all cases when
        using the full series length.

        Parameters
        ----------
        X : 3D np.array (any number of dimensions, equal length series)
                of shape [n_instances, n_dimensions, series_length]
            or 2D np.array (univariate, equal length series)
                of shape [n_instances, series_length]
            or pd.DataFrame with each column a dimension, each cell a pd.Series
                (any number of dimensions, equal or unequal length series)
            or of any other supported Panel mtype
                for list of mtypes, see datatypes.SCITYPE_REGISTER
                for specifications, see examples/AA_datatypes_and_datasets.ipynb

        Returns
        -------
        y : 1D np.array of int, of shape [n_instances] - predicted class labels
            indices correspond to instance indices in X
        decisions : 1D bool array
            An array of booleans, containing the decision of whether a prediction is
            safe to use or not.
            i-th entry is the classifier decision that i-th instance safe to use
        """
        self.check_is_fitted()

        # boilerplate input checks for predict-like methods
        X = self._check_convert_X_for_predict(X)

        return self._predict(X)

    def update_predict(self, X) -> tuple[np.ndarray, np.ndarray]:
        """Update label prediction for sequences in X at a larger series length.

        Uses information stored in the classifiers state from previous predictions and
        updates at shorter series lengths. Update will only accept cases which have not
        yet had a decision made, cases which have had a positive decision should be
        removed from the input with the row ordering preserved.

        If no state information is present, predict will be called instead.

        Prediction updates will return -1 for cases which it cannot make a decision on
        yet. The output is only guaranteed to return a valid class label for all cases
        when using the full series length.

        Parameters
        ----------
        X : 3D np.array (any number of dimensions, equal length series)
                of shape [n_instances, n_dimensions, series_length]
            or 2D np.array (univariate, equal length series)
                of shape [n_instances, series_length]
            or pd.DataFrame with each column a dimension, each cell a pd.Series
                (any number of dimensions, equal or unequal length series)
            or of any other supported Panel mtype
                for list of mtypes, see datatypes.SCITYPE_REGISTER
                for specifications, see examples/AA_datatypes_and_datasets.ipynb

        Returns
        -------
        y : 1D np.array of int, of shape [n_instances] - predicted class labels
            indices correspond to instance indices in X
        decisions : 1D bool array
            An array of booleans, containing the decision of whether a prediction is
            safe to use or not.
            i-th entry is the classifier decision that i-th instance safe to use
        """
        self.check_is_fitted()

        # boilerplate input checks for predict-like methods
        X = self._check_convert_X_for_predict(X)

        if self.state_info is None:
            return self._predict(X)
        else:
            return self._update_predict(X)

    def predict_proba(self, X) -> tuple[np.ndarray, np.ndarray]:
        """Predicts labels probabilities for sequences in X.

        Early classifiers can predict at series lengths shorter than the train data
        series length.

        Probability predictions will return [-1]*n_classes_ for cases which it cannot
        make a decision on yet. The output is only guaranteed to return a valid class
        label for all cases when using the full series length.

        Parameters
        ----------
        X : 3D np.array (any number of dimensions, equal length series)
                of shape [n_instances, n_dimensions, series_length]
            or 2D np.array (univariate, equal length series)
                of shape [n_instances, series_length]
            or pd.DataFrame with each column a dimension, each cell a pd.Series
                (any number of dimensions, equal or unequal length series)
            or of any other supported Panel mtype
                for list of mtypes, see datatypes.SCITYPE_REGISTER
                for specifications, see examples/AA_datatypes_and_datasets.ipynb

        Returns
        -------
        y : 2D array of shape [n_instances, n_classes] - predicted class probabilities
            1st dimension indices correspond to instance indices in X
            2nd dimension indices correspond to possible labels (integers)
            (i, j)-th entry is predictive probability that i-th instance is of class j
        decisions : 1D bool array
            An array of booleans, containing the decision of whether a prediction is
            safe to use or not.
            i-th entry is the classifier decision that i-th instance safe to use
        """
        self.check_is_fitted()

        # boilerplate input checks for predict-like methods
        X = self._check_convert_X_for_predict(X)

        return self._predict_proba(X)

    def update_predict_proba(self, X) -> tuple[np.ndarray, np.ndarray]:
        """Update label probabilities for sequences in X at a larger series length.

        Uses information stored in the classifiers state from previous predictions and
        updates at shorter series lengths. Update will only accept cases which have not
        yet had a decision made, cases which have had a positive decision should be
        removed from the input with the row ordering preserved.

        If no state information is present, predict_proba will be called instead.

        Probability predictions updates will return [-1]*n_classes_ for cases which it
        cannot make a decision on yet. The output is only guaranteed to return a valid
        class label for all cases when using the full series length.

        Parameters
        ----------
        X : 3D np.array (any number of dimensions, equal length series)
                of shape [n_instances, n_dimensions, series_length]
            or 2D np.array (univariate, equal length series)
                of shape [n_instances, series_length]
            or pd.DataFrame with each column a dimension, each cell a pd.Series
                (any number of dimensions, equal or unequal length series)
            or of any other supported Panel mtype
                for list of mtypes, see datatypes.SCITYPE_REGISTER
                for specifications, see examples/AA_datatypes_and_datasets.ipynb

        Returns
        -------
        y : 2D array of shape [n_instances, n_classes] - predicted class probabilities
            1st dimension indices correspond to instance indices in X
            2nd dimension indices correspond to possible labels (integers)
            (i, j)-th entry is predictive probability that i-th instance is of class j
        decisions : 1D bool array
            An array of booleans, containing the decision of whether a prediction is
            safe to use or not.
            i-th entry is the classifier decision that i-th instance safe to use
        """
        self.check_is_fitted()

        # boilerplate input checks for predict-like methods
        X = self._check_convert_X_for_predict(X)

        if self.state_info is None:
            return self._predict_proba(X)
        else:
            return self._update_predict_proba(X)

    def score(self, X, y) -> tuple[float, float, float]:
        """Scores predicted labels against ground truth labels on X.

        Parameters
        ----------
        X : 3D np.array (any number of dimensions, equal length series)
                of shape [n_instances, n_dimensions, series_length]
            or 2D np.array (univariate, equal length series)
                of shape [n_instances, series_length]
            or pd.DataFrame with each column a dimension, each cell a pd.Series
                (any number of dimensions, equal or unequal length series)
            or of any other supported Panel mtype
                for list of mtypes, see datatypes.SCITYPE_REGISTER
                for specifications, see examples/AA_datatypes_and_datasets.ipynb
        y : 1D np.ndarray of int, of shape [n_instances] - class labels (ground truth)
            indices correspond to instance indices in X

        Returns
        -------
        Tuple of floats, harmonic mean, accuracy and earliness scores of predict(X) vs y
        """
        self.check_is_fitted()

        # boilerplate input checks for predict-like methods
        X = self._check_convert_X_for_predict(X)

        return self._score(X, y)

    def get_state_info(self):
        """Return the state information generated from the last predict/update call.

        Returns
        -------
        An array containing the state info for each decision in X from update and
        predict methods. Contains classifier dependent information for future decisions
        on the data and information on when a cases decision has been made. Each row
        contains information for a case from the latest decision on its safety made in
        update/predict. Successive updates are likely to remove rows from the
        state_info, as it will only store as many rows as there are input instances to
        update/predict.
        """
        return self.state_info

    def reset_state_info(self):
        """Reset the state information used in update methods."""
        self.state_info = None

    @staticmethod
    def filter_X(X, decisions):
        """Remove True cases from X given a boolean array of decisions."""
        inv_dec = np.invert(decisions)
        return X[inv_dec]

    @staticmethod
    def filter_X_y(X, y, decisions):
        """Remove True cases from X and y given a boolean array of decisions."""
        inv_dec = np.invert(decisions)
        return X[inv_dec], y[inv_dec]

    @staticmethod
    def split_indices(indices, decisions):
        """Split a list of indices given a boolean array of decisions."""
        inv_dec = np.invert(decisions)
        return indices[inv_dec], indices[decisions]

    @staticmethod
    def split_indices_and_filter(X, indices, decisions):
        """Remove True cases and split a list of indices given an array of decisions."""
        inv_dec = np.invert(decisions)
        return X[inv_dec], indices[inv_dec], indices[decisions]

    @abstractmethod
    def _fit(self, X, y):
        """Fit time series classifier to training data.

        Abstract method, must be implemented.

        Parameters
        ----------
        X : guaranteed to be of a type in self.get_tag("X_inner_mtype")
            if self.get_tag("X_inner_mtype") = "numpy3D":
                3D np.ndarray of shape = [n_instances, n_dimensions, series_length]
            if self.get_tag("X_inner_mtype") = "nested_univ":
                pd.DataFrame with each column a dimension, each cell a pd.Series
            for list of other mtypes, see datatypes.SCITYPE_REGISTER
            for specifications, see examples/AA_datatypes_and_datasets.ipynb
        y : 1D np.array of int, of shape [n_instances] - class labels for fitting
            indices correspond to instance indices in X

        Returns
        -------
        self :
            Reference to self.

        Notes
        -----
        Changes state by creating a fitted model that updates attributes
        ending in "_" and sets is_fitted flag to True.
        """
        ...

    @abstractmethod
    def _predict(self, X) -> tuple[np.ndarray, np.ndarray]:
        """Predicts labels for sequences in X.

        Abstract method, must be implemented.

        This method should update state_info with any values necessary to make future
        decisions. It is recommended that the previous time stamp used for each case
        should be stored in the state_info. The number of rows in state_info after the
        method has been called should match the number of input rows.

        Parameters
        ----------
        X : guaranteed to be of a type in self.get_tag("X_inner_mtype")
            if self.get_tag("X_inner_mtype") = "numpy3D":
                3D np.ndarray of shape = [n_instances, n_dimensions, series_length]
            if self.get_tag("X_inner_mtype") = "nested_univ":
                pd.DataFrame with each column a dimension, each cell a pd.Series
            for list of other mtypes, see datatypes.SCITYPE_REGISTER
            for specifications, see examples/AA_datatypes_and_datasets.ipynb

        Returns
        -------
        y : 1D np.array of int, of shape [n_instances] - predicted class labels
            indices correspond to instance indices in X
        decisions : 1D bool array
            An array of booleans, containing the decision of whether a prediction is
            safe to use or not.
            i-th entry is the classifier decision that i-th instance safe to use
        """
        ...

    @abstractmethod
    def _update_predict(self, X) -> tuple[np.ndarray, np.ndarray]:
        """Update label prediction for sequences in X at a larger series length.

        Abstract method, must be implemented.

        Uses information from previous decisions stored in state_info. This method
        should update state_info with any values necessary to make future decisions.
        It is recommended that the previous time stamp used for each case should be
        stored in the state_info. The number of rows in state_info after the method has
        been called should match the number of input rows.

        Parameters
        ----------
        X : guaranteed to be of a type in self.get_tag("X_inner_mtype")
            if self.get_tag("X_inner_mtype") = "numpy3D":
                3D np.ndarray of shape = [n_instances, n_dimensions, series_length]
            if self.get_tag("X_inner_mtype") = "nested_univ":
                pd.DataFrame with each column a dimension, each cell a pd.Series
            for list of other mtypes, see datatypes.SCITYPE_REGISTER
            for specifications, see examples/AA_datatypes_and_datasets.ipynb

        Returns
        -------
        y : 1D np.array of int, of shape [n_instances] - predicted class labels
            indices correspond to instance indices in X
        decisions : 1D bool array
            An array of booleans, containing the decision of whether a prediction is
            safe to use or not.
            i-th entry is the classifier decision that i-th instance safe to use
        """
        ...

    def _predict_proba(self, X) -> tuple[np.ndarray, np.ndarray]:
        """Predicts labels probabilities for sequences in X.

        This method should update state_info with any values necessary to make future
        decisions. It is recommended that the previous time stamp used for each case
        should be stored in the state_info. The number of rows in state_info after the
        method has been called should match the number of input rows.

        Default behaviour is to call _predict and set the predicted class probability
        to 1, other class probabilities to 0 if a positive decision is made. Override if
        better estimates are obtainable.

        Parameters
        ----------
        X : guaranteed to be of a type in self.get_tag("X_inner_mtype")
            if self.get_tag("X_inner_mtype") = "numpy3D":
                3D np.ndarray of shape = [n_instances, n_dimensions, series_length]
            if self.get_tag("X_inner_mtype") = "nested_univ":
                pd.DataFrame with each column a dimension, each cell a pd.Series
            for list of other mtypes, see datatypes.SCITYPE_REGISTER
            for specifications, see examples/AA_datatypes_and_datasets.ipynb

        Returns
        -------
        y : 2D array of shape [n_instances, n_classes] - predicted class probabilities
            1st dimension indices correspond to instance indices in X
            2nd dimension indices correspond to possible labels (integers)
            (i, j)-th entry is predictive probability that i-th instance is of class j
        decisions : 1D bool array
            An array of booleans, containing the decision of whether a prediction is
            safe to use or not.
            i-th entry is the classifier decision that i-th instance safe to use
        """
        dists = np.zeros((X.shape[0], self.n_classes_))
        preds, decisions = self._predict(X)
        for i in range(0, X.shape[0]):
            if decisions[i]:
                dists[i, self._class_dictionary[preds[i]]] = 1
            else:
                dists[i, :] = -1

        return dists, decisions

    def _update_predict_proba(self, X) -> tuple[np.ndarray, np.ndarray]:
        """Update label probabilities for sequences in X at a larger series length.

        Uses information from previous decisions stored in state_info. This method
        should update state_info with any values necessary to make future decisions.
        It is recommended that the previous time stamp used for each case should be
        stored in the state_info. The number of rows in state_info after the method has
        been called should match the number of input rows.

        Default behaviour is to call _update_predict and set the predicted class
        probability to 1, other class probabilities to 0 if a positive decision is made.
        Override if better estimates are obtainable.

        Parameters
        ----------
        X : guaranteed to be of a type in self.get_tag("X_inner_mtype")
            if self.get_tag("X_inner_mtype") = "numpy3D":
                3D np.ndarray of shape = [n_instances, n_dimensions, series_length]
            if self.get_tag("X_inner_mtype") = "nested_univ":
                pd.DataFrame with each column a dimension, each cell a pd.Series
            for list of other mtypes, see datatypes.SCITYPE_REGISTER
            for specifications, see examples/AA_datatypes_and_datasets.ipynb

        Returns
        -------
        y : 2D array of shape [n_instances, n_classes] - predicted class probabilities
            1st dimension indices correspond to instance indices in X
            2nd dimension indices correspond to possible labels (integers)
            (i, j)-th entry is predictive probability that i-th instance is of class j
        decisions : 1D bool array
            An array of booleans, containing the decision of whether a prediction is
            safe to use or not.
            i-th entry is the classifier decision that i-th instance safe to use
        """
        dists = np.zeros((X.shape[0], self.n_classes_))
        preds, decisions = self._update_predict(X)
        for i in range(0, X.shape[0]):
            if decisions[i]:
                dists[i, self._class_dictionary[preds[i]]] = 1
            else:
                dists[i, :] = -1

        return dists, decisions

    @abstractmethod
    def _score(self, X, y) -> tuple[float, float, float]:
        """Scores predicted labels against ground truth labels on X.

        Abstract method, must be implemented.

        Parameters
        ----------
        X : guaranteed to be of a type in self.get_tag("X_inner_mtype")
            if self.get_tag("X_inner_mtype") = "numpy3D":
                3D np.ndarray of shape = [n_instances, n_dimensions, series_length]
            if self.get_tag("X_inner_mtype") = "nested_univ":
                pd.DataFrame with each column a dimension, each cell a pd.Series
            for list of other mtypes, see datatypes.SCITYPE_REGISTER
            for specifications, see examples/AA_datatypes_and_datasets.ipynb
        y : 1D np.array of int, of shape [n_instances] - class labels for fitting
            indices correspond to instance indices in X

        Returns
        -------
        Tuple of floats, harmonic mean, accuracy and earliness scores of predict(X) vs y
        """
        ...

    def _check_convert_X_for_predict(self, X):
        """Input checks, capability checks, repeated in all predict/score methods.

        Parameters
        ----------
        X : any object (to check/convert)
            should be of a supported Panel mtype or 2D numpy.ndarray

        Returns
        -------
        X: an object of a supported Panel mtype, numpy3D if X was a 2D numpy.ndarray

        Raises
        ------
        ValueError if X is of invalid input data type, or there is not enough data
        ValueError if the capabilities in self._tags do not handle the data.
        """
        _check_convert_X_for_predict = BaseClassifier._check_convert_X_for_predict
        return _check_convert_X_for_predict(self, X)

    def _check_capabilities(self, X_metadata):
        """Check whether this classifier can handle the data characteristics.

        Parameters
        ----------
        X_metadata : dict with metadata for X returned by datatypes.check_is_scitype

        Raises
        ------
        ValueError if the capabilities in self._tags do not handle the data.
        """
        _check_capabilities = BaseClassifier._check_capabilities
        return _check_capabilities(self, X_metadata)

    def _convert_X(self, X, X_mtype):
        """Convert equal length series from DataFrame to numpy array or vice versa.

        Parameters
        ----------
        X : input data for the classifier
        X_mtype : str, a Panel mtype string, e.g., "pd_multiindex", "numpy3D"

        Returns
        -------
        X : input X converted to type in "X_inner_mtype" tag
            usually a pd.DataFrame (nested) or 3D np.ndarray
            Checked and possibly converted input data
        """
        _convert_X = BaseClassifier._convert_X
        return _convert_X(self, X, X_mtype)

    def _check_y(self, y=None, return_to_mtype=False):
        """Check and coerce X/y for fit/transform functions.

        Parameters
        ----------
        y : pd.DataFrame, pd.Series or np.ndarray
        return_to_mtype : bool
            whether to return the mtype of y output

        Returns
        -------
        y_inner : object of sktime compatible time series type
            can be Series, Panel, Hierarchical
        y_metadata : dict
            metadata of y, returned by check_is_scitype
        y_mtype : str, only returned if return_to_mtype=True
            mtype of y_inner, after convert
        """
        _check_y = BaseClassifier._check_y
        return _check_y(self, y, return_to_mtype=return_to_mtype)

    def _check_input(self, X, y=None, enforce_min_instances=1, return_metadata=True):
        """Check whether input X and y are valid formats with minimum data.

        Raises a ValueError if the input is not valid.

        Parameters
        ----------
        X : check whether conformant with any sktime Panel mtype specification
        y : check whether a pd.Series or np.array
        enforce_min_instances : int, optional (default=1)
            check there are a minimum number of instances.
        return_metadata : bool, str, or list of str
            metadata fields to return with X_metadata, input to check_is_scitype

        Returns
        -------
        metadata : dict with metadata for X returned by datatypes.check_is_scitype

        Raises
        ------
        ValueError
            If y or X is invalid input data type, or there is not enough data
        """
        _check_input = BaseClassifier._check_input
        return _check_input(self, X, y, enforce_min_instances, return_metadata)

    def _internal_convert(self, X, y=None):
        """Convert X and y if necessary as a user convenience.

        Convert X to a 3D numpy array if already a 2D and convert y into an 1D numpy
        array if passed as a Series.

        Parameters
        ----------
        X : an object of a supported Panel mtype, or 2D numpy.ndarray
        y : np.ndarray or pd.Series

        Returns
        -------
        X: an object of a supported Panel mtype, numpy3D if X was a 2D numpy.ndarray
        y: np.ndarray
        """
        _internal_convert = BaseClassifier._internal_convert
        return _internal_convert(self, X, y)
