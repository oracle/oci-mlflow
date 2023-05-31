========
Concepts
========

MLflow is a framework that enables engineering teams to easily move workflows from R&D to staging to
production, overcoming one of the common data science problems of model reproducibility and productionalization.

For a detailed view of the key concepts of MLflow please refer to their
documentation: `https://mlflow.org/docs/latest/concepts.html <https://mlflow.org/docs/latest/concepts.html>`_

**Benefits Of Using MLflow**


- Open Source tool for MLops, removing vendor lock-in, works from laptop to cloud all with the same CLI/SDK
- Supports many Tools and Frameworks, for example Spark, Keras, Pytorch, Tensorflow, XGBoost, etc. When using one of these
  frameworks, you can use MLflow to track your experiments, store your models, and deploy them to a variety of platforms where much of this happens
  automatically for you. Using `mlflow.<framework>.autolog <https://mlflow.org/docs/latest/python_api/mlflow.html?highlight=autolog#mlflow.autolog>`_
  the framework will automatically log parameters & metrics.
- Highly Customizable, thanks to Conda and Containers models and training workloads are extremely flexible.
- It is ideal for data science projects, because the workflow enabled by MLflow scales from a data scientist tinkering
  on the weekend with some new ideas, to running a reproducible training experiment on large scale data in the cloud.
- Focuses on the entire Machine learning lifecycle, by providing tools for data preparation, model training,
  model evaluation, model serving, and model deployment MLflow is a complete solution for the entire ML lifecycle,
  working together with Oracle OCI Data Science to scale and deploy highly available models in the cloud.
- Custom Visualization, the MLflow interface allows you to create custom visualizations for an experiment to compare
  different runs and models.
