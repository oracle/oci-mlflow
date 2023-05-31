#!/usr/bin/env python
# -*- coding: utf-8; -*-

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import re
import os
from dataclasses import dataclass
from typing import Any, Callable
from functools import wraps

TELEMETRY_ARGUMENT_NAME = "telemetry"


def telemetry(
    entry_point: str = "",
    name: str = "oci.mlflow",
    environ_variable: str = "EXTRA_USER_AGENT_INFO",
) -> Callable:
    """The telemetry decorator.

    Parameters
    ----------
    entry_point: str
        The entry point of the telemetry.
        Example: "plugin=project&action=run"
    name: str
        The name of the telemetry.
    environ_variable: (str, optional). Defaults to `EXTRA_USER_AGENT_INFO`.
        The name of the environment variable to capture the telemetry sequence.

    Examples
    --------
    >>> @telemetry(entry_point="plugin=project&action=run",name="oci.mlflow")
    ... def test_function(**kwargs)
    ...     print(kwargs.pop("telemetry"))
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            telemetry = Telemetry(name=name, environ_variable=environ_variable).begin(
                entry_point
            )
            try:
                # Injects the telemetry object to the kwargs arguments of the decorated function.
                # This is necessary to be able to add some extra information to the telemetry
                # from the decorated function.
                return func(*args, **{**kwargs, **{TELEMETRY_ARGUMENT_NAME: telemetry}})
            except:
                raise
            finally:
                telemetry.clean()

        return wrapper

    return decorator


@dataclass
class Telemetry:
    """Class to capture telemetry sequence into the environment variable.
    It is doing nothing but adding the telemetry sequence in the specified environment variable.

    Attributes
    ----------
    name: str
        The name of the telemetry.
    environ_variable: (str, optional). Defaults to `EXTRA_USER_AGENT_INFO`.
        The name of the environment variable to capture the telemetry sequence.
    """

    name: str
    environ_variable: str = "EXTRA_USER_AGENT_INFO"

    def __post_init__(self):
        self.name = self._prepare(self.name)
        os.environ[self.environ_variable] = ""

    def clean(self) -> "Telemetry":
        """Cleans the associated environment variable.

        Returns
        -------
        self: Telemetry
            An instance of the Telemetry.
        """
        os.environ[self.environ_variable] = ""
        return self

    def _begin(self):
        self.clean()
        os.environ[self.environ_variable] = self.name

    def begin(self, value: str = "") -> "Telemetry":
        """The method that needs to be invoked in the beginning of the capturing telemetry sequence.
        It resets the value of the associated environment variable.

        Parameters
        ----------
        value: str
            The value that need to be added to the telemetry.

        Returns
        -------
        self: Telemetry
            An instance of the Telemetry.
        """
        return self.clean().add(self.name).add(value)

    def add(self, value: str) -> "Telemetry":
        """Adds the new value to the telemetry.

        Parameters
        ----------
        value: str
            The value that need to be added to the telemetry.

        Returns
        -------
        self: Telemetry
            An instance of the Telemetry.
        """
        if not os.environ.get(self.environ_variable):
            self._begin()

        if value:
            current_value = os.environ.get(self.environ_variable, "")
            new_value = self._prepare(value)
            if new_value not in current_value:
                os.environ[self.environ_variable] = f"{current_value}&{new_value}"
        return self

    def print(self) -> None:
        """Prints the telemetry sequence from environment variable."""
        print(f"{self.environ_variable} = {os.environ.get(self.environ_variable)}")

    def _prepare(self, value: str):
        """Replaces the special characters with the `_` in the input string."""
        return (
            re.sub("[^a-zA-Z0-9\.\-\_\&\=]", "_", re.sub(r"\s+", " ", value))
            if value
            else ""
        )
