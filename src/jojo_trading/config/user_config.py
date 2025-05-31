"""
JoJoTrading 用戶自定義配置管理系統
===============================

允許用戶創建、保存、管理和分享自定義配置預設，包含：
1. 成長股篩選自定義參數
2. DCF 估值自定義配置
3. FCF 計算優化自定義設定
4. 配置預設的命名、保存、載入和分享

功能特點：
- 直觀的配置編輯界面
- 本地儲存和雲端同步
- 配置匯入/匯出
- 配置版本管理
- 社群配置分享
"""

import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import hashlib

@dataclass
class UserConfigMetadata:
    """用戶配置元數據"""
    id: str
    name: str
    description: str
    author: str
    created_at: str
    modified_at: str
    version: str
    tags: List[str]
    is_public: bool
    usage_count: int
    rating: float
    category: str  # 'growth', 'dcf', 'integrated', 'industry_specific'

@dataclass
class UserGrowthConfig:
    """用戶自定義成長股配置"""
    name: str
    description: str
    revenue_cagr_enabled: bool
    revenue_cagr_threshold: float
    revenue_cagr_years: int
    eps_cagr_enabled: bool
    eps_cagr_threshold: float
    eps_cagr_years: int
    roe_enabled: bool
    roe_threshold: float
    debt_ratio_enabled: bool
    debt_ratio_threshold: float
    margin_enabled: bool
    margin_threshold: float
    logic_operator: str
    min_market_cap: Optional[float]
    exclude_industries: List[str]
    custom_conditions: List[Dict[str, Any]]

@dataclass
class UserDCFConfig:
    """用戶自定義DCF配置"""
    name: str
    description: str
    short_term_growth_rate: float
    terminal_growth_rate: float
    risk_preference: float
    projection_years: int
    screening_threshold: float
    enable_anomaly_detection: bool
    anomaly_threshold: float
    calculation_method: str
    fcf_optimization: Dict[str, Any]
    industry_adjustments: Dict[str, Any]

@dataclass
class UserIntegratedConfig:
    """用戶整合配置（成長股+DCF+其他）"""
    metadata: UserConfigMetadata
    growth_config: UserGrowthConfig
    dcf_config: UserDCFConfig
    additional_filters: Dict[str, Any]
    backtest_results: Optional[Dict[str, Any]]

class UserConfigManager:
    """用戶配置管理器"""
    
    def __init__(self, config_dir: str = "user_configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # 創建子目錄
        (self.config_dir / "presets").mkdir(exist_ok=True)
        (self.config_dir / "templates").mkdir(exist_ok=True)
        (self.config_dir / "shared").mkdir(exist_ok=True)
        (self.config_dir / "backups").mkdir(exist_ok=True)
        
        self.index_file = self.config_dir / "index.json"
        self._load_index()
    
    def _load_index(self):
        """載入配置索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
        else:
            self.index = {
                'configs': {},
                'categories': ['growth', 'dcf', 'integrated', 'industry_specific'],
                'tags': [],
                'last_updated': datetime.now().isoformat()
            }
    
    def _save_index(self):
        """保存配置索引"""
        self.index['last_updated'] = datetime.now().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def create_config(
        self,
        name: str,
        description: str,
        author: str,
        category: str,
        growth_config: UserGrowthConfig,
        dcf_config: UserDCFConfig,
        tags: List[str] = None,
        is_public: bool = False
    ) -> str:
        """
        創建新的用戶配置
        
        Returns:
            配置ID
        """
        config_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        metadata = UserConfigMetadata(
            id=config_id,
            name=name,
            description=description,
            author=author,
            created_at=now,
            modified_at=now,
            version="1.0",
            tags=tags or [],
            is_public=is_public,
            usage_count=0,
            rating=0.0,
            category=category
        )
        
        integrated_config = UserIntegratedConfig(
            metadata=metadata,
            growth_config=growth_config,
            dcf_config=dcf_config,
            additional_filters={},
            backtest_results=None
        )
        
        # 保存配置文件
        config_file = self.config_dir / "presets" / f"{config_id}.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(integrated_config), f, ensure_ascii=False, indent=2)
        
        # 更新索引
        self.index['configs'][config_id] = asdict(metadata)
        
        # 更新標籤列表
        for tag in tags or []:
            if tag not in self.index['tags']:
                self.index['tags'].append(tag)
        
        self._save_index()
        
        return config_id
    
    def load_config(self, config_id: str) -> Optional[UserIntegratedConfig]:
        """載入配置"""
        config_file = self.config_dir / "presets" / f"{config_id}.json"
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建物件結構
            metadata = UserConfigMetadata(**data['metadata'])
            growth_config = UserGrowthConfig(**data['growth_config'])
            dcf_config = UserDCFConfig(**data['dcf_config'])
            
            config = UserIntegratedConfig(
                metadata=metadata,
                growth_config=growth_config,
                dcf_config=dcf_config,
                additional_filters=data.get('additional_filters', {}),
                backtest_results=data.get('backtest_results')
            )
            
            # 更新使用次數
            self.index['configs'][config_id]['usage_count'] += 1
            self._save_index()
            
            return config
            
        except Exception as e:
            print(f"載入配置錯誤: {e}")
            return None
    
    def save_config(self, config: UserIntegratedConfig) -> bool:
        """保存配置更新"""
        try:
            config.metadata.modified_at = datetime.now().isoformat()
            
            config_file = self.config_dir / "presets" / f"{config.metadata.id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self.index['configs'][config.metadata.id] = asdict(config.metadata)
            self._save_index()
            
            return True
        except Exception as e:
            print(f"保存配置錯誤: {e}")
            return False
    
    def delete_config(self, config_id: str) -> bool:
        """刪除配置"""
        try:
            config_file = self.config_dir / "presets" / f"{config_id}.json"
            if config_file.exists():
                # 移動到備份目錄而不是直接刪除
                backup_file = self.config_dir / "backups" / f"{config_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                config_file.rename(backup_file)
            
            # 從索引中移除
            if config_id in self.index['configs']:
                del self.index['configs'][config_id]
                self._save_index()
            
            return True
        except Exception as e:
            print(f"刪除配置錯誤: {e}")
            return False
    
    def list_configs(
        self,
        category: Optional[str] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None
    ) -> List[UserConfigMetadata]:
        """列出配置"""
        configs = []
        
        for config_data in self.index['configs'].values():
            metadata = UserConfigMetadata(**config_data)
            
            # 篩選條件
            if category and metadata.category != category:
                continue
            if author and metadata.author != author:
                continue
            if is_public is not None and metadata.is_public != is_public:
                continue
            if tags:
                if not any(tag in metadata.tags for tag in tags):
                    continue
            
            configs.append(metadata)
        
        # 按修改時間排序
        configs.sort(key=lambda x: x.modified_at, reverse=True)
        return configs
    
    def search_configs(self, query: str) -> List[UserConfigMetadata]:
        """搜尋配置"""
        results = []
        query_lower = query.lower()
        
        for config_data in self.index['configs'].values():
            metadata = UserConfigMetadata(**config_data)
            
            # 在名稱、描述、標籤中搜尋
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                results.append(metadata)
        
        return results
    
    def duplicate_config(self, config_id: str, new_name: str, new_author: str) -> Optional[str]:
        """複製配置"""
        original_config = self.load_config(config_id)
        if not original_config:
            return None
        
        # 創建新配置
        new_config_id = self.create_config(
            name=new_name,
            description=f"基於 '{original_config.metadata.name}' 的副本",
            author=new_author,
            category=original_config.metadata.category,
            growth_config=original_config.growth_config,
            dcf_config=original_config.dcf_config,
            tags=original_config.metadata.tags.copy(),
            is_public=False
        )
        
        return new_config_id
    
    def export_config(self, config_id: str, export_path: str) -> bool:
        """匯出配置"""
        config = self.load_config(config_id)
        if not config:
            return False
        
        try:
            export_data = {
                'jojo_trading_config': True,
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'config': asdict(config)
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"匯出配置錯誤: {e}")
            return False
    
    def import_config(self, import_path: str, author: str) -> Optional[str]:
        """匯入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if not import_data.get('jojo_trading_config'):
                raise ValueError("無效的JoJoTrading配置文件")
            
            config_data = import_data['config']
            
            # 重建配置物件
            growth_config = UserGrowthConfig(**config_data['growth_config'])
            dcf_config = UserDCFConfig(**config_data['dcf_config'])
            
            # 創建新配置（使用匯入者作為作者）
            new_config_id = self.create_config(
                name=f"[匯入] {config_data['metadata']['name']}",
                description=config_data['metadata']['description'],
                author=author,
                category=config_data['metadata']['category'],
                growth_config=growth_config,
                dcf_config=dcf_config,
                tags=config_data['metadata']['tags'],
                is_public=False
            )
            
            return new_config_id
            
        except Exception as e:
            print(f"匯入配置錯誤: {e}")
            return None
    
    def create_template(self, template_name: str, base_config_id: str) -> bool:
        """創建配置模板"""
        config = self.load_config(base_config_id)
        if not config:
            return False
        
        try:
            # 移除個人化資訊
            template_data = asdict(config)
            template_data['metadata']['author'] = 'template'
            template_data['metadata']['is_public'] = True
            template_data['metadata']['usage_count'] = 0
            template_data['metadata']['rating'] = 0.0
            
            template_file = self.config_dir / "templates" / f"{template_name}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"創建模板錯誤: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取配置統計資訊"""
        total_configs = len(self.index['configs'])
        categories = {}
        authors = {}
        public_configs = 0
        
        for config_data in self.index['configs'].values():
            category = config_data['category']
            author = config_data['author']
            
            categories[category] = categories.get(category, 0) + 1
            authors[author] = authors.get(author, 0) + 1
            
            if config_data['is_public']:
                public_configs += 1
        
        return {
            'total_configs': total_configs,
            'public_configs': public_configs,
            'private_configs': total_configs - public_configs,
            'categories': categories,
            'top_authors': sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5],
            'total_tags': len(self.index['tags']),
            'most_used_tags': self.index['tags'][:10]
        }
    
    def save_growth_config(self, growth_config: UserGrowthConfig) -> bool:
        """保存成長股配置"""
        try:
            # 創建元數據
            metadata = UserConfigMetadata(
                id=str(uuid.uuid4()),
                name=growth_config.name,
                description=growth_config.description,
                author="系統用戶",
                created_at=datetime.now().isoformat(),
                modified_at=datetime.now().isoformat(),
                version="1.0",
                tags=["成長股"],
                is_public=False,
                usage_count=0,
                rating=0.0,
                category="growth"
            )
            
            # 創建整合配置（只有成長股部分）
            integrated_config = UserIntegratedConfig(
                metadata=metadata,
                growth_config=growth_config,
                dcf_config=UserDCFConfig(
                    name="默認DCF配置",
                    description="默認DCF配置",
                    short_term_growth_rate=0.10,
                    terminal_growth_rate=0.035,
                    risk_preference=0.07,
                    projection_years=5,
                    screening_threshold=0.15,
                    enable_anomaly_detection=True,
                    anomaly_threshold=1.5,
                    calculation_method="enhanced",
                    fcf_optimization={},
                    industry_adjustments={}
                ),
                additional_filters={},
                backtest_results=None
            )
            
            return self.save_config(integrated_config)
        except Exception as e:
            print(f"保存成長股配置失敗: {e}")
            return False
    
    def save_dcf_config(self, dcf_config: UserDCFConfig) -> bool:
        """保存DCF配置"""
        try:
            # 創建元數據
            metadata = UserConfigMetadata(
                id=str(uuid.uuid4()),
                name=dcf_config.name,
                description=dcf_config.description,
                author="系統用戶",
                created_at=datetime.now().isoformat(),
                modified_at=datetime.now().isoformat(),
                version="1.0",
                tags=["DCF估值"],
                is_public=False,
                usage_count=0,
                rating=0.0,
                category="dcf"
            )
            
            # 創建整合配置（只有DCF部分）
            integrated_config = UserIntegratedConfig(
                metadata=metadata,
                growth_config=UserGrowthConfig(
                    name="默認成長股配置",
                    description="默認成長股配置",
                    revenue_cagr_enabled=True,
                    revenue_cagr_threshold=0.15,
                    revenue_cagr_years=3,
                    eps_cagr_enabled=True,
                    eps_cagr_threshold=0.15,
                    eps_cagr_years=3,
                    roe_enabled=True,
                    roe_threshold=0.15,
                    debt_ratio_enabled=False,
                    debt_ratio_threshold=0.5,
                    margin_enabled=False,
                    margin_threshold=0.1,
                    logic_operator="AND",
                    min_market_cap=None,
                    exclude_industries=[],
                    custom_conditions=[]
                ),
                dcf_config=dcf_config,
                additional_filters={},
                backtest_results=None
            )
            
            return self.save_config(integrated_config)
        except Exception as e:
            print(f"保存DCF配置失敗: {e}")
            return False
    
    def list_all_configs(self) -> List[Dict[str, Any]]:
        """列出所有配置的摘要信息"""
        try:
            configs = self.list_configs()
            return [asdict(config) for config in configs]
        except Exception as e:
            print(f"列出配置失敗: {e}")
            return []
    
    def load_and_apply_config(self, config_id: str, context: Dict[str, Any]) -> bool:
        """載入配置並應用到上下文"""
        try:
            config = self.load_config(config_id)
            if not config:
                return False
            
            # 應用成長股配置
            if config.growth_config:
                growth = config.growth_config
                context.update({
                    'revenue_cagr_enabled': growth.revenue_cagr_enabled,
                    'revenue_cagr_threshold': growth.revenue_cagr_threshold * 100,  # 轉為百分比
                    'eps_cagr_enabled': growth.eps_cagr_enabled,
                    'eps_cagr_threshold': growth.eps_cagr_threshold * 100,
                    'roe_enabled': growth.roe_enabled,
                    'roe_threshold': growth.roe_threshold * 100,
                    'growth_logic_operator': growth.logic_operator,
                    'applied_custom_config': config.metadata.name
                })
            
            # 應用DCF配置
            if config.dcf_config:
                dcf = config.dcf_config
                context.update({
                    'dcf_short_term_growth_rate': dcf.short_term_growth_rate,
                    'dcf_terminal_growth_rate': dcf.terminal_growth_rate,
                    'dcf_risk_preference': dcf.risk_preference,
                    'dcf_projection_years': dcf.projection_years,
                    'dcf_screening_threshold': dcf.screening_threshold,
                    'dcf_enable_anomaly_detection': dcf.enable_anomaly_detection,
                    'applied_custom_config': config.metadata.name
                })
            
            # 更新使用計數
            config.metadata.usage_count += 1
            config.metadata.modified_at = datetime.now().isoformat()
            self.save_config(config)
            
            return True
        except Exception as e:
            print(f"載入並應用配置失敗: {e}")
            return False

def apply_user_config_to_context(config: UserIntegratedConfig, context: Dict[str, Any]) -> Dict[str, Any]:
    """將用戶配置應用到系統上下文"""
    
    # 應用成長股配置
    growth = config.growth_config
    context.update({
        'revenue_cagr_enabled': growth.revenue_cagr_enabled,
        'revenue_cagr_threshold': growth.revenue_cagr_threshold,
        'eps_cagr_enabled': growth.eps_cagr_enabled,
        'eps_cagr_threshold': growth.eps_cagr_threshold,
        'roe_enabled': growth.roe_enabled,
        'roe_threshold': growth.roe_threshold,
        'growth_logic_operator': growth.logic_operator,
        'exclude_industries': growth.exclude_industries
    })
    
    # 應用DCF配置
    dcf = config.dcf_config
    context.update({
        'dcf_short_term_growth_rate': dcf.short_term_growth_rate,
        'dcf_terminal_growth_rate': dcf.terminal_growth_rate,
        'risk_preference': dcf.risk_preference,
        'dcf_projection_years': dcf.projection_years,
        'screening_threshold': dcf.screening_threshold,
        'enable_anomaly_detection': dcf.enable_anomaly_detection,
        'anomaly_threshold': dcf.anomaly_threshold,
        'fcf_optimization': dcf.fcf_optimization
    })
    
    # 應用額外篩選條件
    context.update(config.additional_filters)
    
    # 記錄使用的配置資訊
    context['user_config_applied'] = {
        'config_id': config.metadata.id,
        'config_name': config.metadata.name,
        'config_version': config.metadata.version,
        'applied_at': datetime.now().isoformat()
    }
    
    return context

def create_sample_configs(manager: UserConfigManager):
    """創建範例配置"""
    
    # 範例1：積極成長配置
    aggressive_growth = UserGrowthConfig(
        name="積極成長股篩選",
        description="適合高風險高回報的成長股投資",
        revenue_cagr_enabled=True,
        revenue_cagr_threshold=15.0,
        revenue_cagr_years=3,
        eps_cagr_enabled=True,
        eps_cagr_threshold=20.0,
        eps_cagr_years=3,
        roe_enabled=True,
        roe_threshold=18.0,
        debt_ratio_enabled=True,
        debt_ratio_threshold=50.0,
        margin_enabled=False,
        margin_threshold=0.0,
        logic_operator="OR",
        min_market_cap=100.0,
        exclude_industries=["金融業"],
        custom_conditions=[]
    )
    
    aggressive_dcf = UserDCFConfig(
        name="積極DCF估值",
        description="適合高成長股的DCF參數",
        short_term_growth_rate=0.12,
        terminal_growth_rate=0.04,
        risk_preference=0.09,
        projection_years=5,
        screening_threshold=0.25,
        enable_anomaly_detection=True,
        anomaly_threshold=1.5,
        calculation_method="enhanced",
        fcf_optimization={
            'maintenance_capex_ratio': 0.7,
            'working_capital_limit': 0.25,
            'heavy_asset_threshold': 0.20
        },
        industry_adjustments={}
    )
    
    manager.create_config(
        name="積極成長策略",
        description="適合風險承受度高的投資者，追求高成長股票",
        author="JoJoTrading",
        category="integrated",
        growth_config=aggressive_growth,
        dcf_config=aggressive_dcf,
        tags=["積極", "成長股", "高風險", "科技股"],
        is_public=True
    )
    
    # 範例2：穩健價值配置
    conservative_growth = UserGrowthConfig(
        name="穩健價值篩選",
        description="注重穩定性和價值的保守策略",
        revenue_cagr_enabled=True,
        revenue_cagr_threshold=8.0,
        revenue_cagr_years=3,
        eps_cagr_enabled=True,
        eps_cagr_threshold=10.0,
        eps_cagr_years=3,
        roe_enabled=True,
        roe_threshold=12.0,
        debt_ratio_enabled=True,
        debt_ratio_threshold=30.0,
        margin_enabled=True,
        margin_threshold=8.0,
        logic_operator="AND",
        min_market_cap=50.0,
        exclude_industries=[],
        custom_conditions=[]
    )
    
    conservative_dcf = UserDCFConfig(
        name="穩健DCF估值",
        description="保守的DCF估值參數",
        short_term_growth_rate=0.06,
        terminal_growth_rate=0.025,
        risk_preference=0.06,
        projection_years=4,
        screening_threshold=0.15,
        enable_anomaly_detection=True,
        anomaly_threshold=1.2,
        calculation_method="enhanced",
        fcf_optimization={
            'maintenance_capex_ratio': 0.8,
            'working_capital_limit': 0.35,
            'heavy_asset_threshold': 0.25
        },
        industry_adjustments={}
    )
    
    manager.create_config(
        name="穩健價值策略",
        description="適合保守型投資者，重視穩定性和合理估值",
        author="JoJoTrading",
        category="integrated",
        growth_config=conservative_growth,
        dcf_config=conservative_dcf,
        tags=["穩健", "價值投資", "低風險", "傳統產業"],
        is_public=True
    )

# ============================================
# 使用範例
# ============================================

if __name__ == "__main__":
    # 創建配置管理器
    manager = UserConfigManager()
    
    # 創建範例配置
    create_sample_configs(manager)
    
    # 列出所有配置
    print("📋 用戶配置列表:")
    configs = manager.list_configs()
    for config in configs:
        print(f"  • {config.name} ({config.category}) - {config.author}")
        print(f"    {config.description}")
        print(f"    標籤: {', '.join(config.tags)}")
        print()
    
    # 顯示統計
    stats = manager.get_statistics()
    print("📊 配置統計:")
    print(f"  總配置數: {stats['total_configs']}")
    print(f"  公開配置: {stats['public_configs']}")
    print(f"  私人配置: {stats['private_configs']}")
    print(f"  類別分布: {stats['categories']}")
    print(f"  標籤總數: {stats['total_tags']}")
