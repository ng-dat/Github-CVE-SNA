# Description
This repo aims to crawl data from github network of CVE-related directories
Then, to construct the relationship graph into neo4j schema.  
  
# Running
     - Install requirements, run cmd: pip install -r python_requirement.txt
     - Initialize neo4j
        - Set default admin, run cmd: <NEO4J-HOME>/bin/neo4j-admin set-default-admin neo4j *(1)*
        - Run neo4j console, run cmd: <NEO4J-HOME>/bin/neo4j console
        - Open 1 web browser*(2)* and go to localhost:7474 to visit Neo4j Browser tool. Login to neo4j (default username: neo4j, default password: neo4j)  
        - Create new user: CREATE USER dat1 SET PASSWORD '1'
        - Assign roles for user:  GRANT ROLE admin to dat1 *(1)*
        - Create new database: CREATE DATABASE git2neo *(1)* / Or import current databases.
     - Run github Query
        - Generate new Github Personal access tokens with scopes:
            user
            public_repo
            repo
            repo_deployment
            repo:status
            read:repo_hook
            read:org
            read:public_key
            read:gpg_key
          And replace its in configuration
        - Run query cmd: python git2neo.py
     - Run Analysis functions
        - Sample cypher queries:
            - MATCH (:Person)-[:STARRED]->(r:Repo) CALL { WITH r MATCH (r)<-[:STARRED]-(p) RETURN p LIMIT 5 } RETURN r, p
     
# Notes
  - *(1) Only Enterprise edition has these functionalities, Community edition has to use default single database.*
  - *(2) Sometime, neo4j browser show nothing. This is a bug. Change web browser like Chorme, EE, FireFox,... might help.*  
  
# Acknowledgement
  A great appreciation for **USC GRID-CKID Fall 2020 github-cve-social-graph Team** for developing crawling tools that are utilized in this project.