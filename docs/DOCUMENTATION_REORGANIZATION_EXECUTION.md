# JoJo Trading 文檔重組執行計劃

## 📋 重組目標

優化 `docs/` 目錄結構，消除重複，提升文檔可維護性和可訪問性。

## 🔄 重組方案

### Phase 1: 合併用戶指南
```
當前狀態:
├── guides/
│   ├── STARTUP_GUIDE.md
│   ├── TAIWAN_PRESET_USAGE_GUIDE.md
│   └── ...
└── user_guides/
    ├── QUICK_START.md
    └── README.md

重組後:
└── user_guides/
    ├── README.md (更新為總索引)
    ├── QUICK_START.md (合併啟動指南)
    ├── TAIWAN_PRESET_GUIDE.md (台灣預設功能)
    └── ADVANCED_USAGE.md (進階使用)
```

### Phase 2: 建立部署文檔目錄
```
當前狀態:
├── guides/DEPLOY_TO_GITHUB.md
└── deployment/ (空)

重組後:
└── deployment/
    ├── README.md (部署總覽)
    ├── GITHUB_DEPLOYMENT.md
    ├── LOCAL_DEPLOYMENT.md
    └── PRODUCTION_DEPLOYMENT.md
```

### Phase 3: 建立技術文檔目錄
```
當前狀態:
└── technical/ (空)

重組後:
└── technical/
    ├── README.md (技術文檔索引)
    ├── ARCHITECTURE.md (架構文檔)
    ├── API_REFERENCE.md (API參考)
    └── TROUBLESHOOTING.md (故障排除)
```

### Phase 4: 歸檔已完成計劃
```
當前狀態:
└── plans/
    ├── ADVANCED_CLEANUP_PLAN.md
    └── REFACTORING_PLAN.md

重組後:
├── archive/plans_completed/
│   ├── ADVANCED_CLEANUP_PLAN.md
│   └── REFACTORING_PLAN.md
└── plans/ (只保留未來計劃)
```

## ✅ 執行狀態

- [ ] Phase 1: 合併用戶指南
- [ ] Phase 2: 建立部署文檔
- [ ] Phase 3: 建立技術文檔  
- [ ] Phase 4: 歸檔已完成計劃
- [ ] Phase 5: 更新總索引

---
*創建時間: 2025年6月12日*
