from py2neo import Graph, SystemGraph
from py2neo import Node, Relationship


my_graph = Graph("bolt://localhost:7687", name="git2neo", user="dat1", password="1")
my_graph.delete_all()
# my_graph.schema.create_uniqueness_constraint('Person', 'name')
#my_graph.schema.create_uniqueness_constraint('Movie', 'title')


movies = [
    {"title":"The Matrix", "released" : 1999, "tagline" : "Welcome to the Real World"},
]

people = [
    {"name": "Keanu Reeves", "born":1964},
    {"name": "Carrie-Anne Moss", "born":1967},
]

act_in = [
    {"person": people[0], "movie": movies[0], "role": "Neo"},
    {"person": people[1], "movie": movies[0], "role": "Unk"}
]


tx = my_graph.begin()
for x in movies:
    if (len(my_graph.nodes.match("Movie", title=x["title"])) >0):
        continue
    else:
        newNode = Node("Movie", title=x["title"], released=x["released"], tagline=x["tagline"])
        tx.create(newNode)

for x in people:
    if (len(my_graph.nodes.match("Person", name=x["name"])) > 0):
        continue
    else:
        newNode = Node("Person", name=x["name"], born=x["born"])
        tx.create(newNode)
tx.commit()


tx = my_graph.begin()
for x in act_in:
    person_node = my_graph.nodes.match("Person", name=x["person"]["name"]).first()
    movie_node = my_graph.nodes.match("Movie", title=x["movie"]["title"]).first()
    new_link = Relationship(person_node, "ACTED_IN", movie_node)
    new_link["role"] = x["role"]
    tx.create(new_link)
tx.commit()