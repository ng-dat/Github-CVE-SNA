# Description
This repo aims to crawl data from github network of CVE-related directories
Then, to construct the relationship graph into neo4j schema.  
  
# Installization
 - Install requirements, run cmd: 
        
        pip install -r python_requirement.txt
 - Initialize neo4j
    - Download neo4j source to a folder
     
            <NEO4J-HOME> 
    - Set default admin<sup>(1)</sup>, run cmd: 
            
            <NEO4J-HOME>/bin/neo4j-admin set-default-admin neo4j
    - Run neo4j console, run cmd: 
    
            <NEO4J-HOME>/bin/neo4j console
    - Open web browser<sup>(2)</sup> and go to localhost:7474 to visit Neo4j Browser tool. 
      
      Login to neo4j (default username: neo4j, default password: neo4j)  
    - Create new user, run cypher:
     
            CREATE USER dat1 SET PASSWORD '1'
    - Assign roles for user, run cypher<sup>(1)</sup>:  
            
            GRANT ROLE admin to dat1
    - Create new database<sup>(1)</sup>: 
    
            CREATE DATABASE git2neo
          
       Or import current databases. 
 - Generate new Github Personal access tokens with scopes:
            
        user
        repo
        public_repo    
        repo_deployment
        repo:status
        read:repo_hook
        read:org
        read:public_key
        read:gpg_key
    
     Replace the token in private_config.py
# Running
 - Run github Query        
    - Run cmd: 

            python git2neo.py
 - Run Analysis functions
    - Sample cypher queries<sup>(3)</sup>:
    
            MATCH (:Person)-[]->(r:Repo) 
            CALL { 
              WITH r MATCH (r)<-[]-(p) RETURN p LIMIT 5 
            } 
            CALL { 
              WITH p MATCH (r2)<-[]-(p) RETURN r2 LIMIT 5 
            } 
            RETURN r2, p
      ![alt text](./samples/imgs/SampleQuery5.jpg)
    - Visualize sample histograms, run cmd:
            
            python visualization/histograms.py
# Notes
  - *(1) Only Enterprise edition has these functionalities, Community edition has to use default single database.*
  - *(2) Sometime, neo4j browser show nothing. This seems to be a bug. Move between web browsers like Chorme, EE, FireFox,... might help.*
  - *(3) More sample queries a described in cypher_sample_queries.docx*  
  
# Acknowledgement
  A great appreciation for **USC GRID-CKID Fall 2020 github-cve-social-graph Team** for developing crawling tools that are utilized in this project.
