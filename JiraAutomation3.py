import requests
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# -------- CONFIG --------
JIRA_URL = "https://your-domain.atlassian.net"  # Jira base URL
EMAIL = "your.email@example.com"               # Jira login email
API_TOKEN = "your_api_token_here"              # API token (https://id.atlassian.com/manage/api-tokens)

# Build your JQL filter:
# All issues from PROJ1, and only PROJ2 where Team[Dropdown] = 6785
jql = '(project = PROJ1) OR (project = PROJ2 AND "Team[Dropdown]" = 6785)'
# ------------------------

search_url = f"{JIRA_URL}/rest/api/2/search"

# 1. Fetch all issues (with pagination)
all_issues = []
start_at = 0
max_results = 100  # can be up to 1000 on Server
while True:
    params = {
        "jql": jql,
        "startAt": start_at,
        "maxResults": max_results,
        "fields": "issuelinks"  # only fetch needed field
    }
    resp = requests.get(
        search_url,
        params=params,
        auth=(EMAIL, API_TOKEN),
        headers={"Accept": "application/json"}
    )
    resp.raise_for_status()
    data = resp.json()
    issues = data.get("issues", [])
    if not issues:
        break
    all_issues.extend(issues)
    start_at += len(issues)
    if start_at >= data['total']:
        break

print(f"Fetched {len(all_issues)} issues")

# 2. Extract inter-project dependencies
rows = []
for issue in all_issues:
    src_key = issue['key']
    src_proj = src_key.split("-")[0]

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
            tgt_proj = linked_key.split("-")[0]

            # Only inter-project links
            if tgt_proj != src_proj:
                rows.append({
                    "SourceIssue": src_key,
                    "SourceProject": src_proj,
                    "LinkType": link_type,
                    "TargetIssue": linked_key,
                    "TargetProject": tgt_proj
                })

df = pd.DataFrame(rows)
print("Inter-project dependencies:")
print(df.head())

# 3. Build and draw network graph
G = nx.DiGraph()
for _, row in df.iterrows():
    G.add_node(row['SourceIssue'], project=row['SourceProject'])
    G.add_node(row['TargetIssue'], project=row['TargetProject'])
    G.add_edge(row['SourceIssue'], row['TargetIssue'], label=row['LinkType'])

# assign colours by project
projects = list({data['project'] for _, data in G.nodes(data=True)})
color_map = {}
palette = plt.cm.get_cmap('tab10', len(projects))
for i, proj in enumerate(projects):
    color_map[proj] = palette(i)

node_colors = [color_map[G.nodes[n]['project']] for n in G.nodes()]

plt.figure(figsize=(14, 9))
pos = nx.spring_layout(G, k=0.6, iterations=50)
nx.draw(G, pos,
        with_labels=True,
        node_color=node_colors,
        node_size=1600,
        font_size=8,
        arrows=True)
edge_labels = nx.get_edge_attributes(G, 'label')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
plt.title("Jira Inter-Project Dependency Graph", fontsize=14)
plt.axis('off')
plt.tight_layout()
plt.show()
