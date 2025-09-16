import requests
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

JIRA_URL = "https://jira.mycompany.com"
PAT_TOKEN = "YOUR_PAT_HERE"
PROJECTS = ["PROJ1","PROJ2","PROJ3"]

# JQL search
jql = f'project in ({",".join(PROJECTS)})'
url = f"{JIRA_URL}/rest/api/2/search"
headers = {"Authorization": f"Bearer {PAT_TOKEN}"}

resp = requests.get(url, headers=headers, params={"jql": jql, "maxResults": 500})
issues = resp.json().get("issues", [])

rows = []
for issue in issues:
    for link in issue['fields'].get('issuelinks', []):
        link_type = None
        linked_key = None
        if 'outwardIssue' in link:
            link_type = link['type']['outward']
            linked_key = link['outwardIssue']['key']
        elif 'inwardIssue' in link:
            link_type = link['type']['inward']
            linked_key = link['inwardIssue']['key']
        if linked_key:
            rows.append({
                "SourceIssue": issue['key'],
                "LinkType": link_type,
                "TargetIssue": linked_key
            })

df = pd.DataFrame(rows)
print(df.head())

G = nx.DiGraph()
for _, row in df.iterrows():
    G.add_edge(row['SourceIssue'], row['TargetIssue'], label=row['LinkType'])

plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, k=0.5, iterations=50)
nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=1500, font_size=8, arrows=True)
edge_labels = nx.get_edge_attributes(G, 'label')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
plt.title("Jira Cross-Project Dependency Graph")
plt.axis('off')
plt.show()
