from datetime import datetime, timedelta
from doltpy.etl import dolthub_loader, DoltLoaderBuilder
from mta.dolt_load import get_loaders as get_mta_loaders
from fx_rates_example.dolt_load import (get_raw_table_loaders as get_fx_rates_raw_loaders,
                                        get_transformed_table_loaders as get_fx_rates_transform_loaders)
from ip_to_country.dolt_load import get_dolt_datasets as get_ip_loaders
from wikipedia.word_frequency.dolt_load import get_wikipedia_loaders
from wikipedia.ngrams.dolt_load import get_dolt_datasets as get_ngram_loaders
from five_thirty_eight.polls import get_loaders as get_five_thirty_eight_polls_loaders
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from functools import partial


def get_default_args_helper(start_date: datetime):
    return {'owner': 'liquidata-etl',
            'depends_on_past': False,
            'start_date': start_date,
            'email': ['airflow@liquidata.co'],
            'email_on_failure': False,
            'email_on_retry': False,
            'catchup': False,
            'retry_delay': timedelta(minutes=5)}


def get_args_helper(loader_builder: DoltLoaderBuilder, remote_url: str):
    return dict(loader_builder=loader_builder,
                dolt_dir=None,
                clone=True,
                push=True,
                remote_name='origin',
                dry_run=False,
                remote_url=remote_url)


# FX rates DAG
FX_RATES_REPO_PATH = 'oscarbatori/fx-test-data'
fx_rates_dag = DAG('fx_rates',
                   default_args=get_default_args_helper(datetime(2019, 10, 9)),
                   schedule_interval=timedelta(hours=1))


fx_rates_raw_data = PythonOperator(task_id='fx_rates_raw',
                                   python_callable=dolthub_loader,
                                   op_kwargs=get_args_helper(get_fx_rates_raw_loaders, FX_RATES_REPO_PATH),
                                   dag=fx_rates_dag)

fx_rates_averages = PythonOperator(task_id='fx_rates_averages',
                                   python_callable=dolthub_loader,
                                   op_kwargs=get_args_helper(get_fx_rates_transform_loaders, FX_RATES_REPO_PATH),
                                   dag=fx_rates_dag)

fx_rates_averages.set_upstream(fx_rates_raw_data)


# MTA data DAG
MTA_REPO_PATH = 'oscarbatori/mta-data'
mta_dag = DAG('mta_data',
              default_args=get_default_args_helper(datetime(2019, 10, 8)),
              schedule_interval=timedelta(days=1))

raw_mta_data = PythonOperator(task_id='raw_mta_data',
                              python_callable=dolthub_loader,
                              op_kwargs=get_args_helper(get_mta_loaders, MTA_REPO_PATH),
                              dag=mta_dag)

# IP to country mappings
IP_TO_COUNTRY_REPO = 'Liquidata/ip-to-country'
ip_to_country_dag = DAG('ip_to_country',
                        default_args=get_default_args_helper(datetime(2019, 10, 8)),
                        schedule_interval=timedelta(days=1))

raw_ip_to_country = PythonOperator(task_id='ip_to_country',
                                   python_callable=dolthub_loader,
                                   op_kwargs=get_args_helper(get_ip_loaders, IP_TO_COUNTRY_REPO),
                                   dag=ip_to_country_dag)


# WordNet database
word_net_dag = DAG('word_net',
                   default_args=get_default_args_helper(datetime(2019, 10, 22)),
                   schedule_interval=timedelta(days=7))

raw_word_net = BashOperator(task_id='import-data',
                            bash_command='{{conf.get("core", "dags_folder")}}/word_net/import_from_source.pl ',
                            dag=word_net_dag)


# Code Search Net database
code_search_net_dag = DAG('code_search_net',
                         default_args=get_default_args_helper(datetime(2019, 10, 23)),
                         schedule_interval=timedelta(days=7))

code_search_net = BashOperator(
    task_id='import-data',
    bash_command='{{conf.get("core", "dags_folder")}}/code_search_net/import_from_source.pl ',
    dag=code_search_net_dag
)

# USDA All Foods database
usda_all_foods_dag = DAG(
    'usda_all_foods',
    default_args=get_default_args_helper(datetime(2019, 10, 24)),
    schedule_interval=timedelta(days=7)
)

raw_usda_all_foods = BashOperator(
    task_id='import-data',
    bash_command='{{conf.get("core", "dags_folder")}}/usda_all_foods/import_from_source.pl ',
    dag=usda_all_foods_dag
)

# Tatoeba sentence translations
tatoeba_sentence_translations_dag = DAG(
    'tatoeba_sentence_translations',
    default_args=get_default_args_helper(datetime(2019, 10, 21)),
    schedule_interval=timedelta(days=7)
)

raw_tatoeba_sentence_translations = BashOperator(
    task_id='import-data',
    bash_command='{{conf.get("core", "dags_folder")}}/tatoeba_sentence_translations/import-from-source.pl ',
    dag=tatoeba_sentence_translations_dag
)

# Facebook Neural Code Search Evaluation
neural_code_search_eval_dag = DAG('neural_code_search_eval',
                                  default_args=get_default_args_helper(datetime(2019, 10, 25)),
                                  schedule_interval=timedelta(days=7))

raw_neural_code_search_eval = BashOperator(task_id='import-data',
                                           bash_command='{{conf.get("core", "dags_folder")}}/neural_code_search_eval/import_from_source.pl ',
                                           dag=neural_code_search_eval_dag)

# Wikipedia dump variables
DUMP_DATE = datetime.now() - timedelta(days=4)
FORMATTED_DATE = DUMP_DATE.strftime("%Y%m%d")
# XML dumps released on the 1st and 20th of every month. These jobs should run 4 days after.
CRON_FORMAT = '0 8 5,24 * *'

# Wikipedia word frequency
WIKIPEDIA_WORDS_REPO = 'Liquidata/wikipedia-word-frequency'
wikipedia_dag = DAG(
    'wikipedia-word-frequency',
    default_args=get_default_args_helper(datetime(2019, 10, 18)),
    schedule_interval=CRON_FORMAT)

wikipedia_word_frequencies = PythonOperator(task_id='import-data',
                                            python_callable=dolthub_loader,
                                            op_kwargs=get_args_helper(partial(get_wikipedia_loaders, FORMATTED_DATE),
                                                                      WIKIPEDIA_WORDS_REPO),
                                            dag=wikipedia_dag)

# Wikipedia ngrams
WIKIPEDIA_NGRAMS_REPO = 'Liquidata/wikipedia-ngrams'
DUMP_TARGET = 'latest'
wikipedia_ngrams_dag = DAG(
    'wikipedia-ngrams',
    default_args=get_default_args_helper(datetime(2019, 11, 5)),
    schedule_interval=CRON_FORMAT
)

wikipedia_ngrams = PythonOperator(task_id='import-data',
                                  python_callable=dolthub_loader,
                                  op_kwargs=get_args_helper(partial(get_ngram_loaders, FORMATTED_DATE, DUMP_TARGET),
                                                            WIKIPEDIA_NGRAMS_REPO),
                                  dag=wikipedia_ngrams_dag)

# Backfill Wikipedia ngrams
wikipedia_ngrams_backfill_dag = DAG(
    'wikipedia-ngrams-backfill',
    default_args=get_default_args_helper(datetime(2019, 12, 2)),
    schedule_interval='@once',
)

dump_dates = ['20190820', '20190901', '20190920', '20191001', '20191020', '20191101', '20191120']
for dump_date in dump_dates:
    wikipedia_ngrams_backfill = PythonOperator(task_id='backfill-data',
                                               python_callable=dolthub_loader,
                                               op_kwargs=get_args_helper(partial(get_ngram_loaders, dump_date, dump_date),
                                                                         WIKIPEDIA_NGRAMS_REPO),
                                               dag=wikipedia_ngrams_backfill_dag)

# FiveThirtyEight polls
FIVE_THIRTY_EIGHT_POLLS_PATH = 'five-thirty-eight/polls'
five_thirty_eight_polls_dag = DAG('five_thirty_eight_polls',
                                  default_args=get_default_args_helper(datetime(2019, 12, 3)),
                                  schedule_interval=timedelta(hours=1))

five_thirty_eight_polls = PythonOperator(task_id='five_thirty_eight_polls',
                                         python_callable=dolthub_loader,
                                         op_kwargs=get_args_helper(get_five_thirty_eight_polls_loaders,
                                                                   FIVE_THIRTY_EIGHT_POLLS_PATH),
                                         dag=five_thirty_eight_polls_dag)
