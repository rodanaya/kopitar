# Data Scaling Architecture - Massive Dataset Handling

## Scale Requirements Overview

### Dataset Magnitude
- **Time Span**: 40+ years (1980-2024)
- **Games**: 85,000+ regular season + 15,000+ playoff games
- **Players**: 1,200+ unique goaltenders
- **Data Points**: 50+ million individual performance records
- **Storage**: 5-10 TB raw data, 2-3 TB processed
- **Growth Rate**: 300+ GB new data per season

### Performance Targets
- **Query Response**: <500ms for 95% of user queries
- **Batch Processing**: Process full season in <2 hours
- **Concurrent Users**: Support 1,000+ simultaneous analysts
- **Data Freshness**: <5 minutes for live games
- **Uptime**: 99.95% availability

---

## Distributed Database Architecture

### Primary Storage: PostgreSQL Cluster

#### Horizontal Partitioning Strategy
```sql
-- Partition by decade for optimal query performance
CREATE TABLE goalie_game_stats_master (
    id BIGSERIAL,
    game_id BIGINT NOT NULL,
    player_id INTEGER NOT NULL,
    game_date DATE NOT NULL,
    -- ... other fields
) PARTITION BY RANGE (game_date);

-- Partition tables by era
CREATE TABLE goalie_stats_1980s 
    PARTITION OF goalie_game_stats_master 
    FOR VALUES FROM ('1980-01-01') TO ('1990-01-01');
    
CREATE TABLE goalie_stats_1990s 
    PARTITION OF goalie_game_stats_master 
    FOR VALUES FROM ('1990-01-01') TO ('2000-01-01');
    
CREATE TABLE goalie_stats_2000s 
    PARTITION OF goalie_game_stats_master 
    FOR VALUES FROM ('2000-01-01') TO ('2010-01-01');
    
CREATE TABLE goalie_stats_2010s 
    PARTITION OF goalie_game_stats_master 
    FOR VALUES FROM ('2010-01-01') TO ('2020-01-01');
    
CREATE TABLE goalie_stats_2020s 
    PARTITION OF goalie_game_stats_master 
    FOR VALUES FROM ('2020-01-01') TO ('2030-01-01');

-- Player-based partitioning for career analysis
CREATE TABLE player_career_stats (
    player_id INTEGER,
    -- ... career metrics
) PARTITION BY HASH (player_id);

-- Create 16 hash partitions for even distribution
CREATE TABLE player_stats_p0 
    PARTITION OF player_career_stats 
    FOR VALUES WITH (MODULUS 16, REMAINDER 0);
-- ... repeat for p1 through p15
```

#### Read Replicas Configuration
```yaml
postgresql_cluster:
  primary:
    role: write_master
    instance_type: db.r6g.8xlarge
    storage: 10TB SSD
    cpu: 32 vCPU
    memory: 256GB
    
  read_replicas:
    - name: analytics_replica_1
      role: analytical_queries
      instance_type: db.r6g.4xlarge
      lag_tolerance: 5s
      
    - name: analytics_replica_2  
      role: historical_analysis
      instance_type: db.r6g.4xlarge
      lag_tolerance: 30s
      
    - name: app_replica
      role: application_queries
      instance_type: db.r6g.2xlarge
      lag_tolerance: 1s
```

### Time-Series Database: InfluxDB Cluster

#### Multi-Node Setup for High Availability
```yaml
influxdb_cluster:
  nodes:
    - node: influx-01
      role: data_node
      retention: 2_years
      shard_duration: 1_week
      
    - node: influx-02
      role: data_node
      retention: 10_years
      shard_duration: 4_weeks
      
    - node: influx-03
      role: meta_node
      backup_role: true
      
  measurements:
    - name: live_game_stats
      retention: 7_days
      precision: second
      
    - name: game_summaries
      retention: 5_years
      precision: minute
      
    - name: career_trends
      retention: infinite
      precision: day
```

#### Data Tiering Strategy
```python
class DataTieringManager:
    def __init__(self):
        self.hot_storage = InfluxDBHot()  # Last 2 seasons
        self.warm_storage = InfluxDBWarm()  # 2-10 years
        self.cold_storage = S3Glacier()  # 10+ years
        
    def tier_data_by_age(self):
        """
        Automatically move data between storage tiers
        """
        # Hot: Current + last season (fast SSD)
        hot_cutoff = datetime.now() - timedelta(days=730)
        
        # Warm: 2-10 years (standard SSD)
        warm_cutoff = datetime.now() - timedelta(days=3650)
        
        # Cold: 10+ years (S3 Glacier)
        cold_cutoff = datetime.now() - timedelta(days=3650)
        
        # Migration jobs
        self.migrate_to_warm(hot_cutoff)
        self.migrate_to_cold(warm_cutoff)
        
    def query_across_tiers(self, query_params: dict):
        """
        Intelligent query routing across storage tiers
        """
        date_range = query_params.get('date_range')
        
        if self.is_recent_data(date_range):
            return self.hot_storage.query(query_params)
        elif self.is_historical_data(date_range):
            return self.warm_storage.query(query_params)
        else:
            # Cross-tier query
            return self.federated_query(query_params)
```

---

## Distributed Computing Framework

### Apache Spark for Big Data Processing

#### Cluster Configuration
```yaml
spark_cluster:
  driver:
    cores: 8
    memory: 32GB
    max_result_size: 8GB
    
  executors:
    instances: 20
    cores: 4
    memory: 16GB
    
  dynamic_allocation:
    enabled: true
    min_executors: 5
    max_executors: 100
    initial_executors: 10
```

#### Optimized Data Processing
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

class MassiveDataProcessor:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("KopitarMassiveAnalysis") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .getOrCreate()
            
    def process_historical_fatigue_analysis(self):
        """
        Process 40 years of data for fatigue patterns
        """
        # Read partitioned data efficiently
        games_df = self.spark.read \
            .format("delta") \
            .option("multiLine", "true") \
            .load("s3://kopitar-data/games/")
            
        # Cache frequently accessed data
        games_df.cache()
        
        # Parallel processing by decade
        decades = ['1980s', '1990s', '2000s', '2010s', '2020s']
        
        decade_results = []
        for decade in decades:
            decade_df = games_df.filter(
                col("game_date").between(f"{decade[:4]}-01-01", f"{int(decade[:4])+10}-01-01")
            )
            
            # Complex fatigue calculations
            result = self.calculate_fatigue_patterns(decade_df)
            decade_results.append(result)
            
        # Union all results
        final_result = decade_results[0]
        for result in decade_results[1:]:
            final_result = final_result.union(result)
            
        return final_result
        
    def calculate_fatigue_patterns(self, df):
        """
        Complex fatigue calculations with window functions
        """
        # Window specifications for rolling calculations
        player_window = Window.partitionBy("player_id").orderBy("game_date")
        
        # Rolling 7-day calculations
        rolling_7d = player_window.rangeBetween(-7*86400, 0)  # 7 days in seconds
        
        result = df.withColumn(
            "games_last_7d", 
            count("*").over(rolling_7d)
        ).withColumn(
            "avg_save_pct_7d",
            avg("save_percentage").over(rolling_7d)
        ).withColumn(
            "total_minutes_7d",
            sum("time_on_ice_seconds").over(rolling_7d)
        ).withColumn(
            "fatigue_index",
            # Complex fatigue calculation
            (col("games_last_7d") * 0.3 + 
             col("total_minutes_7d") / 1800 * 0.4 +  # Normalize minutes
             lag("save_percentage", 1).over(player_window) * -0.3)
        )
        
        return result
```

### Dask for Python-Native Scaling

#### Distributed Computing Setup
```python
import dask.dataframe as dd
from dask.distributed import Client, LocalCluster
from dask import delayed

class DaskDataProcessor:
    def __init__(self):
        # Create cluster with 16 workers
        self.cluster = LocalCluster(
            n_workers=16,
            threads_per_worker=4,
            memory_limit='8GB',
            processes=True
        )
        self.client = Client(self.cluster)
        
    def process_player_careers_parallel(self, player_ids: list):
        """
        Process individual player careers in parallel
        """
        # Create delayed tasks for each player
        tasks = []
        for player_id in player_ids:
            task = delayed(self.analyze_single_career)(player_id)
            tasks.append(task)
            
        # Execute all tasks in parallel
        results = dd.compute(*tasks, scheduler='distributed')
        
        return results
        
    def analyze_single_career(self, player_id: int):
        """
        Comprehensive career analysis for single player
        """
        # Load player data
        player_data = self.load_player_data(player_id)
        
        # Calculate career metrics
        career_metrics = {
            'fatigue_resistance': self.calculate_fatigue_resistance(player_data),
            'peak_performance_windows': self.find_peak_windows(player_data),
            'decline_patterns': self.analyze_decline(player_data),
            'recovery_efficiency': self.calculate_recovery_rates(player_data)
        }
        
        return career_metrics
        
    def massive_correlation_analysis(self):
        """
        Calculate correlations across entire dataset
        """
        # Load data as Dask DataFrame
        df = dd.read_parquet('s3://kopitar-data/processed/')
        
        # Select numeric columns for correlation
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        # Compute correlation matrix (distributed)
        correlation_matrix = df[numeric_cols].corr().compute()
        
        return correlation_matrix
```

---

## Caching and Memory Optimization

### Multi-Layer Caching Strategy

#### Redis Cluster for Hot Data
```python
class DistributedCaching:
    def __init__(self):
        self.redis_cluster = RedisCluster(
            startup_nodes=[
                {"host": "redis-01", "port": 7000},
                {"host": "redis-02", "port": 7000},
                {"host": "redis-03", "port": 7000},
            ],
            decode_responses=True,
            skip_full_coverage_check=True
        )
        
        self.cache_policies = {
            'player_recent_stats': {'ttl': 300, 'compression': True},
            'team_season_summary': {'ttl': 3600, 'compression': True},
            'historical_trends': {'ttl': 86400, 'compression': False},
            'fatigue_predictions': {'ttl': 1800, 'compression': True}
        }
        
    def cache_with_compression(self, key: str, data: dict, policy: str):
        """
        Cache data with optional compression for large objects
        """
        cache_config = self.cache_policies[policy]
        
        if cache_config['compression']:
            # Compress large datasets
            compressed_data = self.compress_data(data)
            self.redis_cluster.setex(
                key, 
                cache_config['ttl'], 
                compressed_data
            )
        else:
            self.redis_cluster.setex(
                key,
                cache_config['ttl'],
                json.dumps(data)
            )
            
    def get_cached_data(self, key: str, policy: str):
        """
        Retrieve and decompress cached data
        """
        cached = self.redis_cluster.get(key)
        if not cached:
            return None
            
        cache_config = self.cache_policies[policy]
        
        if cache_config['compression']:
            return self.decompress_data(cached)
        else:
            return json.loads(cached)
```

#### Application-Level Caching
```python
from functools import lru_cache
from cachetools import TTLCache
import threading

class InMemoryCache:
    def __init__(self):
        # Thread-safe TTL cache
        self.cache = TTLCache(maxsize=10000, ttl=300)
        self.lock = threading.RLock()
        
    @lru_cache(maxsize=1000)
    def get_player_career_summary(self, player_id: int):
        """
        Cached player career summary (never changes)
        """
        return self.calculate_career_summary(player_id)
        
    def get_cached_or_compute(self, cache_key: str, compute_func, *args):
        """
        Generic cache-or-compute pattern
        """
        with self.lock:
            if cache_key in self.cache:
                return self.cache[cache_key]
                
            result = compute_func(*args)
            self.cache[cache_key] = result
            return result
```

---

## Stream Processing for Real-Time Data

### Apache Kafka for Data Streaming

#### Topic Configuration
```yaml
kafka_topics:
  live_games:
    partitions: 16
    replication_factor: 3
    retention_ms: 604800000  # 7 days
    
  player_updates:
    partitions: 8
    replication_factor: 3
    retention_ms: 86400000   # 1 day
    
  fatigue_alerts:
    partitions: 4
    replication_factor: 3
    retention_ms: 259200000  # 3 days
```

#### Real-Time Processing Pipeline
```python
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import asyncio

class RealTimeProcessor:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['kafka-01:9092', 'kafka-02:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            batch_size=16384,
            linger_ms=10
        )
        
        self.consumer = KafkaConsumer(
            'live_games',
            bootstrap_servers=['kafka-01:9092', 'kafka-02:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='fatigue_analyzer'
        )
        
    async def process_live_game_stream(self):
        """
        Process live game data for real-time fatigue analysis
        """
        for message in self.consumer:
            game_data = message.value
            
            # Extract goalie performance
            goalie_stats = self.extract_goalie_stats(game_data)
            
            # Calculate real-time fatigue
            fatigue_update = await self.calculate_live_fatigue(goalie_stats)
            
            # Publish fatigue alert if threshold exceeded
            if fatigue_update['fatigue_index'] > 80:
                await self.publish_fatigue_alert(fatigue_update)
                
            # Update real-time dashboard
            await self.update_live_dashboard(fatigue_update)
            
    async def publish_fatigue_alert(self, fatigue_data: dict):
        """
        Publish high fatigue alerts
        """
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'player_id': fatigue_data['player_id'],
            'fatigue_index': fatigue_data['fatigue_index'],
            'alert_level': 'high' if fatigue_data['fatigue_index'] > 90 else 'medium',
            'recommendation': 'consider_rest' if fatigue_data['fatigue_index'] > 85 else 'monitor'
        }
        
        self.producer.send('fatigue_alerts', value=alert)
```

---

## Query Optimization and Indexing

### Advanced Indexing Strategy

```sql
-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_goalie_stats_player_date_perf 
    ON goalie_game_stats (player_id, game_date DESC, save_percentage);
    
CREATE INDEX CONCURRENTLY idx_goalie_stats_team_season 
    ON goalie_game_stats (team_id, season, is_starter);
    
CREATE INDEX CONCURRENTLY idx_goalie_stats_fatigue_lookup 
    ON goalie_game_stats (player_id, game_date) 
    INCLUDE (time_on_ice_seconds, shots_against, days_rest);

-- Partial indexes for specific use cases
CREATE INDEX CONCURRENTLY idx_recent_games 
    ON goalie_game_stats (player_id, game_date DESC) 
    WHERE game_date >= CURRENT_DATE - INTERVAL '2 years';
    
CREATE INDEX CONCURRENTLY idx_high_workload_games 
    ON goalie_game_stats (player_id, game_date, time_on_ice_seconds) 
    WHERE time_on_ice_seconds > 3000;  -- >50 minutes

-- Expression indexes for calculated fields
CREATE INDEX CONCURRENTLY idx_save_percentage_rounded 
    ON goalie_game_stats (ROUND(save_percentage::numeric, 3));
    
CREATE INDEX CONCURRENTLY idx_fatigue_category 
    ON goalie_fatigue_metrics ((CASE 
        WHEN fatigue_index >= 80 THEN 'high'
        WHEN fatigue_index >= 60 THEN 'medium'
        ELSE 'low' END));
```

### Query Plan Optimization

```python
class QueryOptimizer:
    def __init__(self):
        self.connection_pool = create_pool(
            database_url,
            min_size=10,
            max_size=50,
            command_timeout=60
        )
        
    def explain_and_optimize(self, query: str):
        """
        Analyze query performance and suggest optimizations
        """
        with self.connection_pool.get_connection() as conn:
            # Get query plan
            explain_result = conn.execute(f"EXPLAIN (ANALYZE, BUFFERS) {query}")
            
            # Analyze for optimization opportunities
            optimizations = self.analyze_query_plan(explain_result)
            
            return optimizations
            
    def analyze_query_plan(self, plan_result):
        """
        Identify optimization opportunities
        """
        suggestions = []
        
        for row in plan_result:
            if 'Seq Scan' in row[0]:
                suggestions.append("Consider adding index for sequential scan")
            elif 'execution time' in row[0] and '>' in row[0]:
                suggestions.append("Query execution time exceeds target")
                
        return suggestions
        
    def materialized_view_candidates(self):
        """
        Identify frequently queried data for materialized views
        """
        candidates = {
            'player_season_aggregates': {
                'query_frequency': 'high',
                'computation_cost': 'medium',
                'refresh_frequency': 'daily'
            },
            'team_defensive_ratings': {
                'query_frequency': 'medium',
                'computation_cost': 'high',
                'refresh_frequency': 'weekly'
            },
            'historical_fatigue_patterns': {
                'query_frequency': 'low',
                'computation_cost': 'very_high',
                'refresh_frequency': 'monthly'
            }
        }
        return candidates
```

---

## Monitoring and Performance Metrics

### System Performance Monitoring

```python
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import psutil
import time

class PerformanceMonitor:
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Database metrics
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query execution time',
            ['query_type', 'table'],
            registry=self.registry
        )
        
        self.db_connections = Gauge(
            'db_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        # Data processing metrics
        self.processing_throughput = Counter(
            'data_processing_records_total',
            'Records processed',
            ['processor_type'],
            registry=self.registry
        )
        
        self.cache_hit_rate = Gauge(
            'cache_hit_rate_percent',
            'Cache hit rate percentage',
            ['cache_type'],
            registry=self.registry
        )
        
        # System resource metrics
        self.memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage',
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage',
            registry=self.registry
        )
        
    def monitor_query_performance(self, query_func, query_type: str, table: str):
        """
        Monitor database query performance
        """
        start_time = time.time()
        try:
            result = query_func()
            duration = time.time() - start_time
            self.db_query_duration.labels(query_type=query_type, table=table).observe(duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.db_query_duration.labels(query_type=f"{query_type}_error", table=table).observe(duration)
            raise
            
    def update_system_metrics(self):
        """
        Update system resource metrics
        """
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage.set(memory.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage.set(cpu_percent)
        
        # Database connections
        active_connections = self.get_db_connection_count()
        self.db_connections.set(active_connections)
```

### Automated Scaling Triggers

```python
class AutoScalingManager:
    def __init__(self):
        self.scaling_policies = {
            'cpu_threshold': 75,  # Scale up if CPU > 75%
            'memory_threshold': 80,  # Scale up if memory > 80%
            'query_latency_threshold': 1000,  # Scale up if queries > 1s
            'connection_threshold': 80  # Scale up if connections > 80%
        }
        
    def check_scaling_conditions(self):
        """
        Evaluate if scaling is needed
        """
        metrics = self.get_current_metrics()
        
        scale_up_triggers = []
        
        if metrics['cpu_usage'] > self.scaling_policies['cpu_threshold']:
            scale_up_triggers.append('high_cpu')
            
        if metrics['memory_usage'] > self.scaling_policies['memory_threshold']:
            scale_up_triggers.append('high_memory')
            
        if metrics['avg_query_latency'] > self.scaling_policies['query_latency_threshold']:
            scale_up_triggers.append('slow_queries')
            
        if scale_up_triggers:
            self.trigger_scaling(scale_up_triggers)
            
    def trigger_scaling(self, triggers: list):
        """
        Execute scaling based on triggers
        """
        scaling_plan = self.create_scaling_plan(triggers)
        
        if 'database' in scaling_plan:
            self.scale_database_replicas(scaling_plan['database'])
            
        if 'compute' in scaling_plan:
            self.scale_compute_nodes(scaling_plan['compute'])
            
        if 'cache' in scaling_plan:
            self.scale_cache_cluster(scaling_plan['cache'])
```

This comprehensive scaling architecture enables the Kopitar project to handle massive historical datasets spanning 40+ years while maintaining sub-second query performance and supporting thousands of concurrent users analyzing goaltender fatigue patterns.