# Dashboard Project Management Feature

## Overview

Add comprehensive project management to the OmniCortex dashboard, including manual project registration, configurable scan directories, and favorites/recent tracking.

**Created:** January 8, 2026
**Status:** Ready for Implementation

---

## Problem Statement

The current dashboard uses automatic filesystem scanning with hardcoded directories (`D:/Projects`, `~/projects`, etc.). This has critical gaps:

1. **Projects outside scanned directories are invisible** unless in `global.db`
2. **No manual registration** - users can't add arbitrary project paths
3. **Hardcoded directory list** - not configurable per-user
4. **No favorites/recents** - all projects treated equally

---

## Solution Architecture

### Data Storage: `~/.omni-cortex/projects.json`

```json
{
  "version": 1,
  "scan_directories": [
    "D:/Projects",
    "~/code",
    "~/workspace"
  ],
  "registered_projects": [
    {
      "path": "C:/Custom/MyProject",
      "display_name": "My Custom Project",
      "added_at": "2026-01-08T10:00:00Z"
    }
  ],
  "favorites": ["D:/Projects/omni-cortex"],
  "recent": [
    {
      "path": "D:/Projects/omni-cortex",
      "last_accessed": "2026-01-08T12:30:00Z"
    }
  ]
}
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage format | JSON file | Simple, human-readable, no DB dependency |
| Location | `~/.omni-cortex/` | Consistent with global.db location |
| Display names | Optional | Allows custom naming, defaults to folder name |
| Recent limit | 10 projects | Balances utility vs clutter |

---

## Implementation Plan

### Phase 1: Backend - Config Manager (New File)

**File:** `dashboard/backend/project_config.py`

```python
"""Project configuration manager for user preferences."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

class RegisteredProject(BaseModel):
    path: str
    display_name: Optional[str] = None
    added_at: datetime

class RecentProject(BaseModel):
    path: str
    last_accessed: datetime

class ProjectConfig(BaseModel):
    version: int = 1
    scan_directories: list[str] = []
    registered_projects: list[RegisteredProject] = []
    favorites: list[str] = []
    recent: list[RecentProject] = []

CONFIG_PATH = Path.home() / ".omni-cortex" / "projects.json"

def get_default_scan_dirs() -> list[str]:
    """Return platform-appropriate default scan directories."""
    import platform
    home = Path.home()

    dirs = [
        str(home / "projects"),
        str(home / "Projects"),
        str(home / "code"),
        str(home / "Code"),
        str(home / "dev"),
        str(home / "workspace"),
    ]

    if platform.system() == "Windows":
        dirs.insert(0, "D:/Projects")

    return [d for d in dirs if Path(d).exists()]

def load_config() -> ProjectConfig:
    """Load config from disk, creating defaults if missing."""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            return ProjectConfig(**data)
        except Exception:
            pass

    # Create default config
    config = ProjectConfig(scan_directories=get_default_scan_dirs())
    save_config(config)
    return config

def save_config(config: ProjectConfig) -> None:
    """Save config to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(config.model_dump_json(indent=2))

def add_registered_project(path: str, display_name: Optional[str] = None) -> bool:
    """Register a new project by path."""
    config = load_config()

    # Validate path has cortex.db
    db_path = Path(path) / ".omni-cortex" / "cortex.db"
    if not db_path.exists():
        return False

    # Check if already registered
    if any(p.path == path for p in config.registered_projects):
        return False

    config.registered_projects.append(RegisteredProject(
        path=path,
        display_name=display_name,
        added_at=datetime.now()
    ))
    save_config(config)
    return True

def remove_registered_project(path: str) -> bool:
    """Remove a registered project."""
    config = load_config()
    original_len = len(config.registered_projects)
    config.registered_projects = [p for p in config.registered_projects if p.path != path]

    if len(config.registered_projects) < original_len:
        save_config(config)
        return True
    return False

def toggle_favorite(path: str) -> bool:
    """Toggle favorite status for a project. Returns new favorite status."""
    config = load_config()

    if path in config.favorites:
        config.favorites.remove(path)
        is_favorite = False
    else:
        config.favorites.append(path)
        is_favorite = True

    save_config(config)
    return is_favorite

def update_recent(path: str) -> None:
    """Update recent projects list."""
    config = load_config()

    # Remove if already in list
    config.recent = [r for r in config.recent if r.path != path]

    # Add to front
    config.recent.insert(0, RecentProject(
        path=path,
        last_accessed=datetime.now()
    ))

    # Keep only last 10
    config.recent = config.recent[:10]

    save_config(config)

def add_scan_directory(directory: str) -> bool:
    """Add a directory to scan list."""
    config = load_config()

    if not Path(directory).is_dir():
        return False

    if directory not in config.scan_directories:
        config.scan_directories.append(directory)
        save_config(config)
        return True
    return False

def remove_scan_directory(directory: str) -> bool:
    """Remove a directory from scan list."""
    config = load_config()

    if directory in config.scan_directories:
        config.scan_directories.remove(directory)
        save_config(config)
        return True
    return False
```

---

### Phase 2: Update Project Scanner

**File:** `dashboard/backend/project_scanner.py`

**Changes:**
1. Import and use `project_config`
2. Use configurable scan directories instead of hardcoded list
3. Merge registered projects with auto-discovered
4. Add `is_favorite` and `is_registered` flags to ProjectInfo

```python
# Key changes to scan_projects():

from project_config import load_config, update_recent

def scan_projects() -> list[ProjectInfo]:
    projects: list[ProjectInfo] = []
    seen_paths: set[str] = set()
    config = load_config()

    # ... existing global index logic ...

    # 2. Use CONFIGURABLE scan directories
    for scan_dir in config.scan_directories:
        scan_path = Path(scan_dir).expanduser()
        if scan_path.exists():
            for db_path in scan_directory_for_cortex(scan_path):
                # ... existing logic ...

    # 3. Add REGISTERED projects (manual additions)
    for reg in config.registered_projects:
        db_path = Path(reg.path) / ".omni-cortex" / "cortex.db"
        if db_path.exists() and str(db_path) not in seen_paths:
            # ... add to projects with is_registered=True ...

    # ... existing global.db fallback ...

    # 4. Annotate favorites
    for p in projects:
        p.is_favorite = p.path in config.favorites

    # 5. Sort: favorites first, then by recency
    projects.sort(key=lambda p: (
        not p.is_global,
        not p.is_favorite,
        -(p.last_modified.timestamp() if p.last_modified else 0)
    ))

    return projects
```

---

### Phase 3: Update Models

**File:** `dashboard/backend/models.py`

Add new fields to `ProjectInfo`:

```python
class ProjectInfo(BaseModel):
    name: str
    path: str
    db_path: str
    last_modified: Optional[datetime] = None
    memory_count: int = 0
    is_global: bool = False
    is_favorite: bool = False        # NEW
    is_registered: bool = False      # NEW
    display_name: Optional[str] = None  # NEW
```

Add new models for config operations:

```python
class ScanDirectory(BaseModel):
    path: str
    project_count: int = 0

class ProjectRegistration(BaseModel):
    path: str
    display_name: Optional[str] = None

class ProjectConfigResponse(BaseModel):
    scan_directories: list[ScanDirectory]
    registered_count: int
    favorites_count: int
```

---

### Phase 4: New API Endpoints

**File:** `dashboard/backend/main.py`

Add new endpoints:

```python
from project_config import (
    load_config, add_registered_project, remove_registered_project,
    toggle_favorite, add_scan_directory, remove_scan_directory
)

# --- Project Management Endpoints ---

@app.get("/api/projects/config")
async def get_project_config():
    """Get project configuration (scan dirs, counts)."""
    config = load_config()
    return {
        "scan_directories": config.scan_directories,
        "registered_count": len(config.registered_projects),
        "favorites_count": len(config.favorites),
    }

@app.post("/api/projects/register")
async def register_project(body: ProjectRegistration):
    """Manually register a project by path."""
    success = add_registered_project(body.path, body.display_name)
    if not success:
        raise HTTPException(400, "Invalid path or already registered")
    return {"success": True}

@app.delete("/api/projects/register")
async def unregister_project(path: str):
    """Remove a registered project."""
    success = remove_registered_project(path)
    if not success:
        raise HTTPException(404, "Project not found")
    return {"success": True}

@app.post("/api/projects/{path:path}/favorite")
async def toggle_project_favorite(path: str):
    """Toggle favorite status for a project."""
    is_favorite = toggle_favorite(path)
    return {"is_favorite": is_favorite}

@app.post("/api/projects/scan-directories")
async def add_scan_dir(directory: str):
    """Add a directory to auto-scan list."""
    success = add_scan_directory(directory)
    if not success:
        raise HTTPException(400, "Invalid directory or already added")
    return {"success": True}

@app.delete("/api/projects/scan-directories")
async def remove_scan_dir(directory: str):
    """Remove a directory from auto-scan list."""
    success = remove_scan_directory(directory)
    if not success:
        raise HTTPException(404, "Directory not found")
    return {"success": True}

@app.post("/api/projects/refresh")
async def refresh_projects():
    """Force rescan of all project directories."""
    projects = scan_projects()
    return {"count": len(projects)}
```

---

### Phase 5: Frontend - Types Update

**File:** `dashboard/frontend/src/types/index.ts`

```typescript
export interface Project {
  name: string
  path: string
  db_path: string
  last_modified: string | null
  memory_count: number
  is_global: boolean
  is_favorite: boolean      // NEW
  is_registered: boolean    // NEW
  display_name: string | null  // NEW
}

export interface ProjectConfig {
  scan_directories: string[]
  registered_count: number
  favorites_count: number
}
```

---

### Phase 6: Frontend - API Service

**File:** `dashboard/frontend/src/services/api.ts`

Add new API calls:

```typescript
export async function getProjectConfig(): Promise<ProjectConfig> {
  const response = await axios.get(`${API_URL}/projects/config`)
  return response.data
}

export async function registerProject(path: string, displayName?: string): Promise<void> {
  await axios.post(`${API_URL}/projects/register`, { path, display_name: displayName })
}

export async function unregisterProject(path: string): Promise<void> {
  await axios.delete(`${API_URL}/projects/register`, { params: { path } })
}

export async function toggleFavorite(path: string): Promise<boolean> {
  const response = await axios.post(`${API_URL}/projects/${encodeURIComponent(path)}/favorite`)
  return response.data.is_favorite
}

export async function addScanDirectory(directory: string): Promise<void> {
  await axios.post(`${API_URL}/projects/scan-directories`, null, { params: { directory } })
}

export async function removeScanDirectory(directory: string): Promise<void> {
  await axios.delete(`${API_URL}/projects/scan-directories`, { params: { directory } })
}

export async function refreshProjects(): Promise<number> {
  const response = await axios.post(`${API_URL}/projects/refresh`)
  return response.data.count
}
```

---

### Phase 7: Frontend - Project Management Modal

**File:** `dashboard/frontend/src/components/ProjectManagementModal.vue`

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import {
  X, FolderPlus, FolderSearch, Star, StarOff,
  Trash2, RefreshCw, Settings
} from 'lucide-vue-next'
import * as api from '@/services/api'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useDashboardStore()

// Tabs
type Tab = 'projects' | 'directories' | 'add'
const activeTab = ref<Tab>('projects')

// Add project form
const newProjectPath = ref('')
const newProjectName = ref('')
const isAdding = ref(false)
const addError = ref('')

// New directory form
const newDirectory = ref('')
const isAddingDir = ref(false)

// Computed
const registeredProjects = computed(() =>
  store.projects.filter(p => p.is_registered)
)

const favoriteProjects = computed(() =>
  store.projects.filter(p => p.is_favorite)
)

// Actions
async function addProject() {
  if (!newProjectPath.value.trim()) return

  isAdding.value = true
  addError.value = ''

  try {
    await api.registerProject(
      newProjectPath.value.trim(),
      newProjectName.value.trim() || undefined
    )
    await store.loadProjects()
    newProjectPath.value = ''
    newProjectName.value = ''
    activeTab.value = 'projects'
  } catch (e) {
    addError.value = 'Failed to add project. Check path has .omni-cortex/cortex.db'
  } finally {
    isAdding.value = false
  }
}

async function removeProject(path: string) {
  try {
    await api.unregisterProject(path)
    await store.loadProjects()
  } catch (e) {
    console.error('Failed to remove project:', e)
  }
}

async function toggleFavorite(project: Project) {
  try {
    await api.toggleFavorite(project.path)
    await store.loadProjects()
  } catch (e) {
    console.error('Failed to toggle favorite:', e)
  }
}

async function addDirectory() {
  if (!newDirectory.value.trim()) return

  isAddingDir.value = true
  try {
    await api.addScanDirectory(newDirectory.value.trim())
    await store.loadProjects()
    newDirectory.value = ''
  } catch (e) {
    console.error('Failed to add directory:', e)
  } finally {
    isAddingDir.value = false
  }
}

async function removeDirectory(dir: string) {
  try {
    await api.removeScanDirectory(dir)
    await store.loadProjects()
  } catch (e) {
    console.error('Failed to remove directory:', e)
  }
}

async function refreshAll() {
  await api.refreshProjects()
  await store.loadProjects()
}
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
        <h2 class="text-lg font-semibold">Project Management</h2>
        <button @click="emit('close')" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b dark:border-gray-700">
        <button
          v-for="tab in ['projects', 'directories', 'add']"
          :key="tab"
          @click="activeTab = tab"
          :class="[
            'px-4 py-3 font-medium capitalize',
            activeTab === tab
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          {{ tab === 'add' ? 'Add Project' : tab }}
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- Projects Tab -->
        <template v-if="activeTab === 'projects'">
          <!-- Favorites Section -->
          <div v-if="favoriteProjects.length" class="mb-6">
            <h3 class="text-sm font-semibold text-gray-500 mb-2">Favorites</h3>
            <div class="space-y-2">
              <div
                v-for="project in favoriteProjects"
                :key="project.path"
                class="flex items-center gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg"
              >
                <Star class="w-5 h-5 text-yellow-500 fill-yellow-500" />
                <div class="flex-1 min-w-0">
                  <div class="font-medium truncate">{{ project.display_name || project.name }}</div>
                  <div class="text-xs text-gray-500 truncate">{{ project.path }}</div>
                </div>
                <button @click="toggleFavorite(project)" class="p-2 hover:bg-yellow-100 rounded">
                  <StarOff class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <!-- All Projects -->
          <h3 class="text-sm font-semibold text-gray-500 mb-2">All Projects</h3>
          <div class="space-y-2">
            <div
              v-for="project in store.projects"
              :key="project.path"
              class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate">
                  {{ project.display_name || project.name }}
                  <span v-if="project.is_registered" class="text-xs text-blue-500 ml-2">(registered)</span>
                </div>
                <div class="text-xs text-gray-500 truncate">{{ project.path }}</div>
              </div>
              <button
                @click="toggleFavorite(project)"
                class="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
              >
                <Star :class="['w-4 h-4', project.is_favorite ? 'text-yellow-500 fill-yellow-500' : 'text-gray-400']" />
              </button>
              <button
                v-if="project.is_registered"
                @click="removeProject(project.path)"
                class="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-500"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </template>

        <!-- Directories Tab -->
        <template v-else-if="activeTab === 'directories'">
          <p class="text-sm text-gray-500 mb-4">
            These directories are automatically scanned for OmniCortex projects.
          </p>

          <!-- Add Directory Form -->
          <div class="flex gap-2 mb-4">
            <input
              v-model="newDirectory"
              placeholder="Enter directory path (e.g., ~/my-projects)"
              class="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <button
              @click="addDirectory"
              :disabled="isAddingDir"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              Add
            </button>
          </div>

          <!-- Directory List -->
          <div class="space-y-2">
            <div
              v-for="dir in store.projectConfig?.scan_directories"
              :key="dir"
              class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <FolderSearch class="w-5 h-5 text-gray-400" />
              <span class="flex-1 truncate">{{ dir }}</span>
              <button
                @click="removeDirectory(dir)"
                class="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-500"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </template>

        <!-- Add Project Tab -->
        <template v-else-if="activeTab === 'add'">
          <p class="text-sm text-gray-500 mb-4">
            Add a project from any location. The path must contain a <code>.omni-cortex/cortex.db</code> file.
          </p>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">Project Path *</label>
              <input
                v-model="newProjectPath"
                placeholder="C:/Users/Me/custom-project"
                class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              />
            </div>

            <div>
              <label class="block text-sm font-medium mb-1">Display Name (optional)</label>
              <input
                v-model="newProjectName"
                placeholder="My Custom Project"
                class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              />
            </div>

            <div v-if="addError" class="text-red-500 text-sm">
              {{ addError }}
            </div>

            <button
              @click="addProject"
              :disabled="isAdding || !newProjectPath.trim()"
              class="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <FolderPlus class="w-5 h-5" />
              Add Project
            </button>
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div class="flex justify-between items-center p-4 border-t dark:border-gray-700">
        <button
          @click="refreshAll"
          class="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
        >
          <RefreshCw class="w-4 h-4" />
          Refresh All
        </button>
        <button
          @click="emit('close')"
          class="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200"
        >
          Done
        </button>
      </div>
    </div>
  </div>
</template>
```

---

### Phase 8: Update ProjectSwitcher

**File:** `dashboard/frontend/src/components/ProjectSwitcher.vue`

Add button to open management modal and favorite indicators:

```vue
<!-- Add to template after "Projects" header -->
<button
  @click="$emit('openManagement')"
  class="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1"
>
  <Settings class="w-3 h-3" />
  Manage
</button>

<!-- Update project item to show favorite star -->
<Star
  v-if="project.is_favorite"
  class="w-4 h-4 text-yellow-500 fill-yellow-500 absolute top-2 right-2"
/>
```

---

### Phase 9: Store Updates

**File:** `dashboard/frontend/src/stores/dashboardStore.ts`

Add config state and actions:

```typescript
// Add to state
const projectConfig = ref<ProjectConfig | null>(null)

// Add action
async function loadProjectConfig() {
  try {
    projectConfig.value = await api.getProjectConfig()
  } catch (e) {
    console.error('Failed to load project config:', e)
  }
}

// Update loadProjects to also load config
async function loadProjects() {
  // ... existing code ...
  await loadProjectConfig()
}

// Expose in return
return {
  // ...
  projectConfig,
  loadProjectConfig,
}
```

---

## File Summary

| File | Action | Description |
|------|--------|-------------|
| `backend/project_config.py` | Create | Config manager (load/save, favorites, etc.) |
| `backend/project_scanner.py` | Modify | Use configurable dirs, add flags |
| `backend/models.py` | Modify | Add new fields to ProjectInfo |
| `backend/main.py` | Modify | Add 6 new API endpoints |
| `frontend/src/types/index.ts` | Modify | Add new Project fields |
| `frontend/src/services/api.ts` | Modify | Add new API functions |
| `frontend/src/components/ProjectManagementModal.vue` | Create | Management UI |
| `frontend/src/components/ProjectSwitcher.vue` | Modify | Add manage button, favorites |
| `frontend/src/stores/dashboardStore.ts` | Modify | Add config state |
| `frontend/src/App.vue` | Modify | Wire up modal |

---

## Testing Strategy

### Backend Tests

1. **Config persistence**: Create/modify/reload config
2. **Project registration**: Valid path, invalid path, duplicate
3. **Favorites toggle**: Add, remove, persistence
4. **Scan directories**: Add, remove, scan results

### Frontend Tests

1. **Modal opens/closes correctly**
2. **Add project form validation**
3. **Favorite toggle updates UI**
4. **Directory management works**
5. **Projects refresh after changes**

### Integration Tests

1. **Add project in one location, verify it appears in switcher**
2. **Favorite persists across page reloads**
3. **Remove scan directory, verify projects disappear**

---

## Success Criteria

- [ ] Users can add projects from any path via UI
- [ ] Scan directories are configurable (add/remove)
- [ ] Favorites are persistent and shown first
- [ ] Recent projects tracked (last 10)
- [ ] All data persists in `~/.omni-cortex/projects.json`
- [ ] Existing auto-discovery still works
- [ ] No breaking changes to current behavior

---

## Future Enhancements (Out of Scope)

- Project groups/folders for organization
- Import/export project config
- Project-level settings (custom MCP config per project)
- File browser integration for path selection
- Drag-and-drop project reordering
