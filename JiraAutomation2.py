from jira import JIRA
import requests
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
JIRA_URL = "https://jira.mycompany.com"          # Your Jira Server URL
PAT_TOKEN = "YOUR_PAT_HERE"                     # Personal Access Token you created
PROJECTS = ["PROJ1", "PROJ2", "PROJ3"]          # Jira project keys
JQL = f'project in ({",".join(PROJECTS)})'      # Filter issues across projects
# ----------------------------

# 1. Build a session that adds the Bearer header
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {PAT_TOKEN}"})
# If your Jira uses a self-signed cert:
session.verify = False  # or path to CA bundle file

# 2. Connect to Jira with that session
jira = JIRA(server=JIRA_URL, session=session)

# 3. Get all issues across projects
issues = jira.search_issues(JQL, maxResults=False)

# 4. Extract dependencies into a DataFrame
rows = []
for issue in issues:
    for link in getattr(issue.fields, 'issuelinks', []):
        link_type = None
        linked_key = None
        if hasattr(link, "outwardIssue"):   # outward (blocks)
            link_type = link.type.outward
            linked_key = link.outwardIssue.key
        elif hasattr(link, "inwardIssue"):  # inward (is blocked by)
            link_type = link.type.inward
            linked_key = link.inwardIssue.key

        if linked_key:
            rows.append({
                "SourceIssue": issue.key,
                "LinkType": link_type,
                "TargetIssue": linked_key
            })

df = pd.DataFrame(rows)

# 5. Show the table
print("Dependency Data Model:")
print(df.head())

# 6. Build a network graph of dependencies
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
