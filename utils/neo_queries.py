from py2neo import Graph, Node, Relationship


def query_all_usernames(neo4j_graph):
    """
    Get users who starred the most number of repositories from Neo4j
    :param neo4j_graph: <type py2neo.Graph>, represents Neo4j database connection
    :param limit_users: <type number>, number of users to query
    :return:
    """
    cypher_query = '''
        MATCH (n:Person) 
        RETURN n.username as name  
    '''
    user_nodes = neo4j_graph.run(cypher_query).data()
    usernames = [str(x['name']) for x in user_nodes]
    return usernames

def query_most_cve_starred_users(neo4j_graph, limit_users):
    """
    Get users who starred the most number of repositories from Neo4j
    :param neo4j_graph: <type py2neo.Graph>, represents Neo4j database connection
    :param limit_users: <type number>, number of users to query
    :return:
    """
    cypher_query = '''
        MATCH (n)-[s:STARRED]->(r:Repo) 
        RETURN n, count(s) AS repos_starred 
        ORDER BY repos_starred desc 
        LIMIT $limit_users_param
    '''
    user_nodes = neo4j_graph.run(cypher_query, parameters={'limit_users_param': limit_users}).data()
    users = [x['n']['username'] for x in user_nodes]
    return users


def query_people_and_starred_links(neo4j_graph):
    """
    """
    cypher_query = '''
        MATCH (n:Person)-[s:STARRED]->()
        WITH n, count(s) as counted
        ORDER BY counted DESC
        RETURN n.username as username, counted
    '''
    user_nodes = neo4j_graph.run(cypher_query).data()
    return user_nodes


def query_repos_and_starred_links(neo4j_graph):
    """
    """
    cypher_query = '''
        MATCH ()-[s:STARRED]->(r:Repo)
        WITH r, count(s) as counted
        ORDER BY counted DESC
        RETURN r.name as reponame, counted
    '''
    nodes = neo4j_graph.run(cypher_query).data()
    return nodes