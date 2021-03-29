import private_config

# neo4j = dict(
#     endpoint = "bolt://localhost:7687",
#     db_name = "git2neo",
#     user_name = "dat1",
#     password = "1",
# )

neo4j = dict(
    endpoint = "bolt://localhost:7687",
    db_name = "neo4j",
    user_name = "neo4j",
    password = private_config.server_neo4j_pass,
)


