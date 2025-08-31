***REMOVED***
//session_start();
require_once 'secrets.inc';
//////////////////////////////////////////////////      connect to db
if ($dbh = mysqli_connect($db_hn, $db_un, $db_pw, $db_db)) {
    $status = 0;
    //mysqli_select_db($dbh, $db_db);
} else {
    //echo 'not a db xxxxxxxxxxxxxxxxx'
    $status = -1;
    die('still problem connecting to MySQL');
}

date_default_timezone_set("Europe/London");
***REMOVED***
