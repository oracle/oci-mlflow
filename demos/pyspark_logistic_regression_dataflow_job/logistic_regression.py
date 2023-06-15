# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/

import click
import mlflow
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import SparkSession
from sklearn.datasets import load_iris


@click.command()
@click.option("--seed", "-s", help="The seed for sampling.", default=20, required=False)
def main(seed):
    spark = SparkSession.builder.getOrCreate()

    df = load_iris(as_frame=True).frame.rename(columns={"target": "label"})
    df = spark.createDataFrame(df)
    df = VectorAssembler(inputCols=df.columns[:-1], outputCol="features").transform(df)
    train, test = df.randomSplit([0.8, 0.2], seed)

    mlflow.pyspark.ml.autolog()

    with mlflow.start_run():
        lor = LogisticRegression(maxIter=5)
        lorModel = lor.fit(train)
        mlflow.log_param("randomSplit", [0.8, 0.2])
        mlflow.log_param("Seed", seed)

    pred = lorModel.transform(test)
    pred.select(lorModel.getPredictionCol()).show(10)
    spark.stop()


if __name__ == "__main__":
    main()
