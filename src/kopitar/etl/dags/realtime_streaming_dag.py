"""
Real-time Streaming DAG

Manages real-time data streams for live NHL games.
Processes live game feeds, updates statistics, and pushes to WebSocket clients.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.providers.redis.operators.redis_publish import RedisPublishOperator
from airflow.utils.task_group import TaskGroup
import pendulum

# Configuration
TIMEZONE = pendulum.timezone("America/New_York")
DEFAULT_ARGS = {
    'owner': 'kopitar-data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1, tzinfo=TIMEZONE),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
    'catchup': False,
    'max_active_runs': 3
}

# DAG definition
dag = DAG(
    'realtime_nhl_streaming',
    default_args=DEFAULT_ARGS,
    description='Real-time NHL game data streaming pipeline',
    schedule_interval=timedelta(minutes=1),  # Run every minute during game times
    tags=['nhl', 'realtime', 'streaming'],
    doc_md=__doc__
)


def detect_live_games(**context):
    """
    Detect currently live NHL games.
    """
    import asyncio
    from kopitar.etl.extractors.nhl_extractor import NHLDataExtractor
    from datetime import date
    
    async def get_live_games():
        async with NHLDataExtractor() as extractor:
            # Get today's schedule
            today = date.today()
            schedule_result = await extractor.extract_schedule(today, today)
            
            if not schedule_result.success:
                return []
            
            # Filter for live games
            live_games = []
            for game in schedule_result.data:
                status = game.get('status', {})
                abstract_state = status.get('abstractGameState', '')
                
                if abstract_state in ['Live', 'Preview']:  # Include games starting soon
                    live_games.append({
                        'game_id': game['nhl_id'],
                        'status': abstract_state,
                        'home_team': game['home_team']['team']['name'],
                        'away_team': game['away_team']['team']['name'],
                        'start_time': game['date_time']
                    })
            
            return live_games
    
    live_games = asyncio.run(get_live_games())
    
    # Store in XCom for downstream tasks
    context['task_instance'].xcom_push(
        key='live_games',
        value=live_games
    )
    
    return f"Found {len(live_games)} live games"


def process_live_game(game_id, **context):
    """
    Process a single live game.
    """
    import asyncio
    from kopitar.etl.extractors.nhl_extractor import NHLDataExtractor
    from kopitar.etl.transformers.realtime_transformer import RealTimeTransformer
    from kopitar.etl.loaders.streaming_loader import StreamingLoader
    
    async def process_game():
        transformer = RealTimeTransformer()
        loader = StreamingLoader()
        
        async with NHLDataExtractor() as extractor:
            # Extract live game data
            live_result = await extractor.extract_live_game(game_id)
            
            if not live_result.success:
                return {
                    'success': False,
                    'error': live_result.error
                }
            
            live_data = live_result.data
            
            # Transform for real-time consumption
            transformed_data = transformer.transform_live_update(live_data)
            
            # Update real-time stores
            updates = {
                'influxdb': await loader.update_influxdb(transformed_data),
                'redis': await loader.update_redis_cache(transformed_data),
                'websocket': await loader.broadcast_update(transformed_data)
            }
            
            return {
                'success': True,
                'game_id': game_id,
                'updates': updates,
                'timestamp': datetime.now().isoformat()
            }
    
    result = asyncio.run(process_game())
    return result


def aggregate_live_updates(**context):
    """
    Aggregate updates from all live games.
    """
    from kopitar.etl.aggregators.realtime_aggregator import RealTimeAggregator
    
    # Get live games list
    live_games = context['task_instance'].xcom_pull(
        task_ids='detect_live_games',
        key='live_games'
    )
    
    if not live_games:
        return "No live games to aggregate"
    
    aggregator = RealTimeAggregator()
    
    # Collect all game updates
    game_updates = []
    for game in live_games:
        game_id = game['game_id']
        update_result = context['task_instance'].xcom_pull(
            task_ids=f'process_game_{game_id}'
        )
        if update_result and update_result.get('success'):
            game_updates.append(update_result)
    
    # Create league-wide aggregations
    aggregations = {
        'live_scores': aggregator.aggregate_live_scores(game_updates),
        'league_stats': aggregator.aggregate_league_stats(game_updates),
        'trending_players': aggregator.identify_trending_players(game_updates),
        'momentum_shifts': aggregator.detect_momentum_shifts(game_updates)
    }
    
    # Store aggregated data
    context['task_instance'].xcom_push(
        key='live_aggregations',
        value=aggregations
    )
    
    return f"Aggregated updates from {len(game_updates)} games"


def update_fatigue_realtime(**context):
    """
    Update real-time fatigue calculations for active players.
    """
    from kopitar.etl.transformers.fatigue_calculator import FatigueCalculator
    
    # Get live games
    live_games = context['task_instance'].xcom_pull(
        task_ids='detect_live_games',
        key='live_games'
    )
    
    if not live_games:
        return "No active games for fatigue updates"
    
    fatigue_calc = FealTimeTransformer()
    
    # Update fatigue for all active players
    active_players = []
    for game in live_games:
        # Get players from each game
        game_players = fatigue_calc.get_active_players(game['game_id'])
        active_players.extend(game_players)
    
    # Calculate real-time fatigue updates
    fatigue_updates = []
    for player_id in set(active_players):  # Remove duplicates
        fatigue_update = fatigue_calc.calculate_realtime_fatigue(
            player_id=player_id,
            timestamp=datetime.now()
        )
        fatigue_updates.append(fatigue_update)
    
    return f"Updated fatigue for {len(fatigue_updates)} players"


def check_stream_health(**context):
    """
    Monitor streaming pipeline health.
    """
    from kopitar.monitoring.stream_monitor import StreamHealthMonitor
    
    monitor = StreamHealthMonitor()
    
    health_metrics = {
        'pipeline_lag': monitor.check_pipeline_lag(),
        'api_response_times': monitor.check_api_performance(),
        'cache_hit_rates': monitor.check_cache_performance(),
        'websocket_connections': monitor.check_websocket_health(),
        'error_rates': monitor.check_error_rates()
    }
    
    # Check for alerts
    alerts = monitor.evaluate_health_metrics(health_metrics)
    
    if alerts:
        # Send alerts to monitoring system
        for alert in alerts:
            monitor.send_alert(alert)
    
    context['task_instance'].xcom_push(
        key='health_metrics',
        value=health_metrics
    )
    
    return f"Stream health check: {len(alerts)} alerts"


# Main tasks
detect_games_task = PythonOperator(
    task_id='detect_live_games',
    python_callable=detect_live_games,
    dag=dag,
    doc_md="Detect currently live NHL games"
)

# Dynamic task group for processing live games
def create_live_game_tasks(**context):
    """
    Dynamically create tasks for each live game.
    """
    from airflow.models import TaskInstance
    
    # Get live games from upstream task
    ti = TaskInstance(detect_games_task, context['execution_date'])
    live_games = ti.xcom_pull(key='live_games')
    
    if not live_games:
        return []
    
    # Create tasks for each game
    game_tasks = []
    for game in live_games:
        game_id = game['game_id']
        task = PythonOperator(
            task_id=f'process_game_{game_id}',
            python_callable=lambda gid=game_id, **ctx: process_live_game(gid, **ctx),
            dag=dag
        )
        game_tasks.append(task)
    
    return game_tasks

aggregate_task = PythonOperator(
    task_id='aggregate_live_updates',
    python_callable=aggregate_live_updates,
    dag=dag,
    doc_md="Aggregate updates from all live games"
)

fatigue_update_task = PythonOperator(
    task_id='update_fatigue_realtime',
    python_callable=update_fatigue_realtime,
    dag=dag,
    doc_md="Update real-time fatigue calculations"
)

health_check_task = PythonOperator(
    task_id='check_stream_health',
    python_callable=check_stream_health,
    dag=dag,
    doc_md="Monitor streaming pipeline health"
)

# Publish aggregated data to Redis pub/sub
publish_updates = RedisPublishOperator(
    task_id='publish_live_updates',
    redis_conn_id='kopitar_redis',
    channel='nhl_live_updates',
    message='{{ ti.xcom_pull(task_ids="aggregate_live_updates", key="live_aggregations") }}',
    dag=dag
)

# Set up dependencies
detect_games_task >> aggregate_task >> [fatigue_update_task, publish_updates]
aggregate_task >> health_check_task

# Conditional execution based on game times
def should_run_streaming(**context):
    """
    Determine if streaming should run based on NHL schedule.
    """
    from datetime import datetime, time
    
    # Get current time in ET
    current_time = datetime.now(TIMEZONE).time()
    current_day = datetime.now(TIMEZONE).weekday()
    
    # NHL games typically run:
    # - Tuesday to Sunday
    # - Between 7 PM and 11 PM ET
    game_start = time(19, 0)  # 7 PM
    game_end = time(23, 30)   # 11:30 PM
    
    # Don't run on Mondays (typically no games)
    if current_day == 0:  # Monday
        return False
    
    # Only run during game hours
    if game_start <= current_time <= game_end:
        return True
    
    # Also run if there are actually live games
    live_games = context['task_instance'].xcom_pull(
        task_ids='detect_live_games',
        key='live_games'
    )
    
    return len(live_games) > 0

# Documentation
dag.doc_md = """
# Real-time NHL Streaming Pipeline

This DAG manages real-time data processing for live NHL games.

## Pipeline Flow

1. **Detect Live Games**: Identify currently active games
2. **Process Games**: Extract and transform live data for each game
3. **Aggregate Updates**: Combine updates for league-wide statistics
4. **Update Fatigue**: Calculate real-time fatigue for active players
5. **Health Check**: Monitor pipeline performance
6. **Publish Updates**: Broadcast to WebSocket clients via Redis

## Execution Schedule

- **Frequency**: Every minute during game times
- **Game Hours**: 7 PM - 11:30 PM ET, Tuesday-Sunday
- **Off-season**: Reduced frequency or paused

## Performance Targets

- **Latency**: < 30 seconds from NHL API to client
- **Throughput**: Support 1000+ concurrent WebSocket connections
- **Reliability**: 99.9% uptime during games

## Monitoring

- Real-time metrics in Grafana
- Alert notifications for delays > 60 seconds
- Health checks every pipeline run

## Manual Controls

Stop streaming:
```bash
airflow dags pause realtime_nhl_streaming
```

Force refresh:
```bash
airflow dags trigger realtime_nhl_streaming
```
"""