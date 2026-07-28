import os
from app import app
from database import db
from models import User, StudyNote

def init_db_and_admin():
    with app.app_context():
        db.create_all()
        
        # Ensure user 'mahesh' exists with password '12341234'
        mahesh = User.query.filter_by(username='mahesh').first()
        if not mahesh:
            mahesh = User(username='mahesh', full_name='Mahesh', role='admin')
            mahesh.set_password('12341234')
            db.session.add(mahesh)
            print("[SUCCESS] Created admin user 'mahesh' (password: 12341234)")
        else:
            mahesh.role = 'admin'
            mahesh.set_password('12341234')
            print("[SUCCESS] Updated admin user 'mahesh' (password: 12341234)")

        # Ensure user 'admin' also exists with password 'admin123'
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', full_name='System Administrator', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print("[SUCCESS] Created admin user 'admin' (password: admin123)")
        else:
            admin_user.role = 'admin'
            admin_user.set_password('admin123')
            print("[SUCCESS] Updated admin user 'admin' (password: admin123)")

        db.session.commit()

        # Seed initial sample study notes if empty
        if StudyNote.query.count() == 0 and mahesh:
            sample_note = StudyNote(
                title="Graph Algorithms Cheatsheet - BFS vs DFS",
                category="Graphs",
                content="""# Graph Traversal Cheatsheet: BFS vs DFS

## 1. Breadth-First Search (BFS)
- **Data Structure**: Uses a Queue (FIFO).
- **Time Complexity**: O(V + E)
- **Space Complexity**: O(V)
- **Use Cases**: Finding shortest path in unweighted graphs, level-order traversal.

```cpp
void bfs(int start, vector<vector<int>>& adj, vector<bool>& visited) {
    queue<int> q;
    q.push(start);
    visited[start] = true;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v : adj[u]) {
            if (!visited[v]) {
                visited[v] = true;
                q.push(v);
            }
        }
    }
}
```

## 2. Depth-First Search (DFS)
- **Data Structure**: Uses Stack / Recursion.
- **Time Complexity**: O(V + E)
- **Space Complexity**: O(V) stack space.
- **Use Cases**: Cycle detection, topological sort, solving mazes/puzzles.""",
                created_by_id=mahesh.id
            )
            db.session.add(sample_note)
            db.session.commit()
            print("[SUCCESS] Sample Study Note seeded!")

        print("[SUCCESS] All admin credentials and initial data updated in database!")

if __name__ == '__main__':
    os.makedirs(app.config['QUESTION_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SUBMISSION_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['NOTE_UPLOAD_FOLDER'], exist_ok=True)
    init_db_and_admin()
