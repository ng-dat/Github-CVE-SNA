import pandas as pd
from py2neo import Graph

import private_config
import config
from utils import git_to_neo_queries

if __name__ == '__main__':
    NUM_OF_CVE_REPOS_TO_CRAWL = 10
    run_first_time = True

    my_graph = Graph(config.neo4j['endpoint'], name=config.neo4j['db_name'], user=config.neo4j['user_name'], password=config.neo4j['password'])
    if (run_first_time):
        my_graph.delete_all()
        # # Uncomment when refreshing database constraints
        # my_graph.schema.create_uniqueness_constraint('Repo', 'name')
        # my_graph.schema.create_uniqueness_constraint('Person', 'username')

    my_token = private_config.github_token


    git_to_neo_queries.query_stargazers_by_cve_repos(my_graph, my_token, limit_stargazers_per_repo_query=50, num_of_repos=5, cve_owner_repos_file='owner_repo.csv')
    git_to_neo_queries.query_l1_repos(my_graph, my_token, limit_users=5, limit_repos_per_user=5, limit_stargazers_per_repo_query=50)


    ## Production size
    # query_cve_repos.gitquery_stargazers_by_cve_repos(my_graph, sub_repos_df, my_token, limit_stargazers_per_repo_query=15000)
    # query_cve_repos.gitquery_l1_repos(my_graph, my_token, limit_users=100, limit_repos_per_user=100, limit_stargazers_per_repo_query=15000)

