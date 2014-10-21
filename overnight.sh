#export TESTDB="GZ"
#export TESTDB="testdb1"
#python dev.py -t gv_scores --allgt --db $TESTDB
#python dev.py -t gv_test --allgt --db $TESTDB

export IBSFLAGS='--noqcache --screen'
#export IBSFLAGS='--noqcache --screen --delete-query-cache'


#export IBSFLAGS=''
#python dev.py -t smk5 --allgt --db PZ_Master0 $IBSFLAGS
#python dev.py -t smk5 --allgt --db GZ_ALL $IBSFLAGS
#python dev.py -t smk_64k --allgt --db PZ_Mothers $IBSFLAGS
#python dev.py -t smk_128k --allgt --db PZ_Mothers $IBSFLAGS
#python dev.py -t smk5 --allgt --db PZ_Mothers $IBSFLAGS

python dev.py -t smk6_overnight --allgt --db GZ_ALL $IBSFLAGS
python dev.py -t smk6_overnight --allgt --db PZ_Master0 $IBSFLAGS
python dev.py -t smk6_overnight --allgt --db PZ_Mothers $IBSFLAGS

export IBSFLAGS=''

#python dev.py -t smk6_overnight --allgt --db GZ_ALL $IBSFLAGS
#python dev.py -t smk6_overnight --allgt --db PZ_Mothers $IBSFLAGS
#python dev.py -t smk6_overnight --allgt --db PZ_Master0 $IBSFLAGS
