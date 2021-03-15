from py2neo import Graph, Node, Relationship


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