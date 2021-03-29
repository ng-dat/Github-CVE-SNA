import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import matplotlib.pyplot as plt
import statistics
from py2neo import Graph

import config
from utils import neo_queries


def show_user_star_connection_histogram(neo4jgraph):
    users = neo_queries.query_people_and_starred_links(neo4jgraph)
    connection_counts  = [x['counted'] for x in users]

    mean = statistics.mean(connection_counts)

    plt.hist(connection_counts, bins=20)
    plt.title("Mean: {:.2f}".format(mean))
    plt.show()


def show_repo_star_connection_histogram(neo4jgraph):
    results = neo_queries.query_repos_and_starred_links(neo4jgraph)
    connection_counts = [x['counted'] for x in results]

    mean = statistics.mean(connection_counts)

    plt.hist(connection_counts, bins=20)
    plt.title("Mean: {:.2f}".format(mean))
    plt.show()


my_graph = Graph(config.neo4j['endpoint'], name=config.neo4j['db_name'], user=config.neo4j['user_name'], password=config.neo4j['password'])
show_user_star_connection_histogram(my_graph)
# show_repo_star_connection_histogram(my_graph)