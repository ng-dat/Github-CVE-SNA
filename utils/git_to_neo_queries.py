"""
    Define Functions to call Github GraphQL then store retrived data to Neo4j Database

"""


import pandas as pd
from py2neo import Node, Relationship
from common.logging import logger

from utils import git_queries, neo_queries


def query_stargazers_by_cve_repos(neo4j_graph,
                                  git_token,
                                  limit_stargazers_per_repo_query=100,
                                  num_of_repos=1,
                                  cve_owner_repos_file='owner_repo.csv'):
    """
    Connect to  Github GraphQL, query stargazers of "CVE" repositories, store to Neo4j database
    :param neo4j_graph: <type py2neo.Graph>, represent Neo4j database connection
    :param git_token: <type string>, github personal access token
    :param limit_stargazers_per_repo_query: <type number>, limited number of stargazer to query from each repository
    :param num_of_repos: <type number>, number of CVE repositories to query
    :param cve_owner_repos_file: <type string>, source of file where store information of CVE repositories.
            File format: csv, 2 columns: "Owner" and "Repo"
    :return:
        return nothing
        The queried stargazer will be added to Neo4j dabase
    """
    repos_df = pd.read_csv(cve_owner_repos_file)
    sub_repos_df = repos_df.iloc[0:num_of_repos]
    repos = sub_repos_df.to_dict('records')
    query_stargazers_by_repos(neo4j_graph, repos, git_token, limit_stargazers_per_repo_query, repo_layer="0")


def query_l1_repos(neo4j_graph,
                   git_token, limit_users = 5,
                   limit_repos_per_user=10,
                   limit_stargazers_per_repo_query=100):
    """
    Get users who starred that most number of CVE repositories in Neo4J DB.
    Query all repositories of those users, call them layered 1 (l1) repositories.
    Query the stargazers of those l1 repositories.
    :param neo4j_graph: <type py2neo.Graph>, represent Neo4j database connection
    :param git_token: <type string>, github personal access token
    :param limit_users: <type number>, limited number of users(who starred CVE repositories) to query.
    :param limit_repos_per_user: <type number>, limited number of l1 repository by each users
    :param limit_stargazers_per_repo_query: <type number>, limited number of stargazers to query from each l1 repository
    :return:
        return nothing
        The queried stargazer will be added to Neo4j dabase
    """

    # Get users who starred that most number of CVE repositories
    users = neo_queries.query_most_cve_starred_users(neo4j_graph, limit_users)

    # Query all repositories of those users,
    print(f'Preparing querying from "{len(users)}" github accounts...')
    query_repos_by_users(neo4j_graph, users, git_token, limit_repos_per_user, limit_stargazers_per_repo_query, expand_repo_layer=True)


def query_stargazers_by_repos(neo4j_graph,
                              repos,
                              git_token,
                              limit_stargazers_per_repo_query,
                              repo_layer):
    """
    Connect to  Github GraphQL, query stargazers of repositories, store to Neo4j database
    """
    headers = {'Authorization': 'token ' + git_token}
    query = """
       query {{
           repository(owner:"{0}", name:"{1}") {{
               stargazers(first:100 {2}) {{
                   pageInfo {{
                       endCursor
                       hasNextPage
                       hasPreviousPage
                       startCursor
                   }}
                   edges {{
                       starredAt
                       node {{
                           login
                           location
                           starredRepositories {{
                               totalCount
                           }}
                       }}
                   }}
               }}
           }}
       }}
       """

    count_repo = 0
    count_error = 0
    error_repos = pd.DataFrame(columns=['Owner', 'Repo', 'Error'])
    for r in repos:
        owner = r['Owner']
        repo = r['Repo']

        try:
            # Add new repo
            if (len(neo4j_graph.nodes.match("Repo", name=repo)) == 0):
                tx = neo4j_graph.begin()
                new_repo_node = Node("Repo", name=repo, type="cve_l"+repo_layer)
                tx.create(new_repo_node)
                tx.commit()
            repo_node = neo4j_graph.nodes.match("Repo", name=repo).first()

            # Query stargazer
            end_cursor = ""  # Start from begining
            count_user = 0
            has_next_page = True
            print(f'Running query for repository "{repo}":')
            while has_next_page and count_user < limit_stargazers_per_repo_query:  ## LIMIT stargazers
                this_query = query.format(owner, repo, end_cursor)
                result = git_queries.run_query(this_query, headers)  # Execute the query
                # print(this_query)
                # print(result)
                has_next_page = result['data']['repository']['stargazers']['pageInfo']['hasNextPage']
                end_cursor = result['data']['repository']['stargazers']['pageInfo']['endCursor']
                end_cursor = ', after: "' + (end_cursor or '') + '"'
                data = result['data']['repository']['stargazers']['edges']

                users_data = [{
                    'username': item['node']['login'],
                    'location': item['node']['location'],
                    'starred_repo_count': item['node']['starredRepositories']['totalCount']
                } for item in data]

                tx = neo4j_graph.begin()
                for user in users_data:
                    if (len(neo4j_graph.nodes.match("Person", username=user['username'])) > 0):
                        user_node = neo4j_graph.nodes.match("Person", username=user['username']).first()
                    else:
                        user_node = Node("Person",
                                         username=user['username'],
                                         location= (user['location'] or ''), # Checking if location null
                                         starred_repo_count=user['starred_repo_count']
                                         )
                        tx.create(user_node)

                    user_repo_link = Relationship(user_node, "STARRED", repo_node)
                    tx.create(user_repo_link)
                tx.commit()

                count_user += len(users_data)
                print(str(count_user) + ' users processed.')

            print(f'Repo: "{repo}" done.')
            count_repo += 1
            print(str(count_repo) + ' repos processed.')
            print('')
            print('')

        except Exception as e:
            count_error += 1
            print('Error with repo: ', repo)
            print(e)
            print('Number of error so far: ' + str(count_error))
            print('')
            print('')
            error_repos = error_repos.append({'Owner': owner, 'Repo': repo, 'Error': e}, ignore_index=True)

        error_repos.to_csv("error/error_gitquery_stargazers_by_repos.csv")


def query_stargazers_by_repo(neo4j_graph,
                              raw_repo,
                              git_token,
                              limit_stargazers_per_repo_query,
                              repo_layer):
    """
    Connect to  Github GraphQL, query stargazers of a SINGLE repository, store to Neo4j database
    """
    headers = {'Authorization': 'token ' + git_token}
    query = """
       query {{
           repository(owner:"{0}", name:"{1}") {{
               stargazers(first:100 {2}) {{
                   pageInfo {{
                       endCursor
                       hasNextPage
                       hasPreviousPage
                       startCursor
                   }}
                   edges {{
                       starredAt
                       node {{
                           login
                           location
                           starredRepositories {{
                               totalCount
                           }}
                       }}
                   }}
               }}
           }}
       }}
       """

    count_repo = 0
    count_error = 0
    error_repos = pd.DataFrame(columns=['Owner', 'Repo', 'User', 'Error'])
    owner = raw_repo['Owner']
    repo = raw_repo['Repo']

    # Add new repo
    if (len(neo4j_graph.nodes.match("Repo", name=repo)) == 0):
        tx = neo4j_graph.begin()
        new_repo_node = Node("Repo", name=repo, type="cve_l"+repo_layer)
        tx.create(new_repo_node)
        tx.commit()
    repo_node = neo4j_graph.nodes.match("Repo", name=repo).first()

    # Query stargazer
    end_cursor = ""  # Start from begining
    count_user = 0
    has_next_page = True
    print(f'Running query for repository "{repo}":')
    while has_next_page and count_user < limit_stargazers_per_repo_query:  ## LIMIT stargazers
        try:
            this_query = query.format(owner, repo, end_cursor)
            result = git_queries.run_query(this_query, headers)  # Execute the query
            # print(this_query)
            # print(result)
            has_next_page = result['data']['repository']['stargazers']['pageInfo']['hasNextPage']
            end_cursor = result['data']['repository']['stargazers']['pageInfo']['endCursor']
            end_cursor = ', after: "' + (end_cursor or '') + '"'
            data = result['data']['repository']['stargazers']['edges']

            users_data = [{
                'username': item['node']['login'],
                'location': item['node']['location'],
                'starred_repo_count': item['node']['starredRepositories']['totalCount']
            } for item in data]

            tx = neo4j_graph.begin()
            for user in users_data:
                if (len(neo4j_graph.nodes.match("Person", username=user['username'])) > 0):
                    user_node = neo4j_graph.nodes.match("Person", username=user['username']).first()
                else:
                    user_node = Node("Person",
                                     username=user['username'],
                                     location= (user['location'] or ''), # Checking if location null
                                     starred_repo_count=user['starred_repo_count']
                                     )
                    tx.create(user_node)

                user_repo_link = Relationship(user_node, "STARRED", repo_node)
                tx.create(user_repo_link)
            tx.commit()

            count_user += len(users_data)
            print(str(count_user) + ' users processed.')
        except Exception as e:
            count_error += 1
            print('Error with repo: ', repo, ' user ', user)
            print(e)
            print('Number of error so far: ' + str(count_error))
            print('')
            print('')
            error_repos = error_repos.append({'Owner': owner, 'Repo': repo, 'User':user, 'Error': e}, ignore_index=True)

    print(f'Repo: "{repo}" done.')
    count_repo += 1
    print(str(count_repo) + ' repos processed.')
    print('')
    print('')

    error_repos.to_csv("error/error_gitquery_stargazers_by_repos.csv")


def query_repos_by_users(neo4j_graph,
                         users,
                         git_token,
                         limit_repos_per_user,
                         limit_stargazers_per_repo_query,
                         expand_repo_layer=False,
                         repo_layer='1'):
    """
    Connect to  Github GraphQL, query repositories of users, store to Neo4j database.
    If expand_repo_layer, query stargazer of those repositories too.
    """
    headers = {'Authorization': 'token ' + git_token}
    query = """
           query {{
               user(login:"{0}") {{
                   repositories(first:100 {1}) {{
                       pageInfo {{
                           endCursor
                           hasNextPage
                           hasPreviousPage
                           startCursor
                       }}
                       edges {{                           
                           node {{
                               name
                           }}
                       }}
                   }}
               }}
           }}
           """
    count_user = 0
    count_error = 0
    errors = pd.DataFrame(columns=['User', 'Error'])
    created_repos = []
    for user in users:
        try:
            # Query repos from Github GraphQL
            print(f'Running query for user "{user}":')
            user_node = neo4j_graph.nodes.match("Person", username=user).first()
            if not user_node:
                continue

            end_cursor = ""  # Start from begining
            count_repos = 0
            has_next_page = True
            while has_next_page and count_repos < limit_repos_per_user:
                this_query = query.format(user, end_cursor)
                result = git_queries.run_query(this_query, headers)  # Execute the query
                # print(this_query)
                # print(result)
                has_next_page = result['data']['user']['repositories']['pageInfo']['hasNextPage']
                end_cursor = result['data']['user']['repositories']['pageInfo']['endCursor']
                end_cursor = ', after: "' + end_cursor + '"'
                data = result['data']['user']['repositories']['edges']

                repos_data = [item['node']['name'].lower() for item in data]

                tx = neo4j_graph.begin()
                for new_repo in repos_data:
                    if len(neo4j_graph.nodes.match("Repo", name=new_repo)) > 0:
                        repo_node = neo4j_graph.nodes.match("Repo", name=new_repo).first()
                    else:
                        repo_node = Node("Repo", name=new_repo, type="cve_l"+repo_layer)
                        tx.create(repo_node)
                    user_repo_link = Relationship(user_node, "CREATED", repo_node)
                    tx.create(user_repo_link)

                    if (expand_repo_layer):
                        created_repos.append({"Owner": user, "Repo": new_repo})
                tx.commit()

                count_repos += len(repos_data)
                print(str(count_repos) + ' repos processed.')

            print(f'User: "{user}" done.')
            count_user += 1
            print(str(count_user) + ' users processed.')
            print('')

        except Exception as e:
            count_error += 1
            print('Error with user: ', user)
            print(e)
            print('Number of error so far: ' + str(count_error))
            print('')
            errors = errors.append({'User': user, 'Error': e}, ignore_index=True)

    errors.to_csv("error/error_gitquery_repos_by_users.csv")

    # Query the stargazers of l1 repos
    if (expand_repo_layer):
        print('')
        print('')
        print('Running query for stargazers of repositories of users:')
        query_stargazers_by_repos(neo4j_graph,
                                  created_repos,
                                  git_token,
                                  limit_stargazers_per_repo_query,
                                  repo_layer="1")


def query_users_relationships(neo4j_graph,
                         users,
                         git_token):
    """
    Connect to  Github GraphQL, check the followers of all current users.
    If there is any following relationship between any 2 users in current network, create FOLLOWED link between them
    :param neo4j_graph:
    :param users:
    :param git_token:
    :return:
    """
    headers = {'Authorization': 'token ' + git_token}
    query = """
           query {{
               user(login:"{0}") {{
                   followers(first:100 {1}) {{
                       pageInfo {{
                           endCursor
                           hasNextPage
                           hasPreviousPage
                           startCursor
                       }}
                       edges {{                           
                           node {{
                                login                                                    
                                location
                                starredRepositories {{
                                   totalCount
                                }}
                           }}
                       }}
                   }}
               }}
           }}
           """
    count_user = 0
    count_error = 0
    errors = pd.DataFrame(columns=['User', 'Error'])
    for user in users:
        try:
            # Query repos from Github GraphQL
            logger.log(f'Running query for user {user}:')
            user_node = neo4j_graph.nodes.match("Person", username=user).first()
            if not user_node:
                logger.log(f'{user} not in the current network. Skipped.')
                continue

            end_cursor = ""  # Start from begining
            count_processed_followers = 0
            count_added_followers = 0
            has_next_page = True
            while has_next_page:
                this_query = query.format(user, end_cursor)
                result = git_queries.run_query(this_query, headers)  # Execute the query

                has_next_page = result['data']['user']['followers']['pageInfo']['hasNextPage']
                end_cursor = result['data']['user']['followers']['pageInfo']['endCursor']
                end_cursor = ', after: "' + end_cursor + '"'
                data = result['data']['user']['followers']['edges']

                followers_data = [{
                    'username': item['node']['login'],
                    'location': item['node']['location'],
                    'starred_repo_count': item['node']['starredRepositories']['totalCount']
                } for item in data]

                tx = neo4j_graph.begin()
                for new_follower in followers_data:
                    if new_follower['username'] in users:
                        follower_node = neo4j_graph.nodes.match("Person", username=new_follower['username']).first()
                        if follower_node == None:
                            continue # Make sure the follower is currently in the network

                        follower_user_link = Relationship(follower_node, "FOLLOWED", user_node)
                        tx.create(follower_user_link)
                        count_added_followers += 1
                    else:
                        continue  # If the follower is not in current network, ignore him
                count_processed_followers += len(followers_data)

                tx.commit()
                logger.log(str(count_added_followers) + ' followers added throughout  ' + str(count_processed_followers) + ' processed.')

            logger.log(f'User: "{user}" done.')
            count_user += 1
            logger.log(str(count_user) + ' users processed.')
            logger.log('')

        except Exception as e:
            count_error += 1
            logger.log('Error with user: ', user)
            logger.log(e)
            logger.log('Number of error so far: ' + str(count_error))
            logger.log('')
            errors = errors.append({'User': user, 'Error': e}, ignore_index=True)

    errors.to_csv("error/error_gitquery_users_followers.csv")

