***REMOVED***
require_once "common.inc";
//$json = file_get_contents('php://input'); // for some reason normal $_POST doesn't work
//$obj = json_decode($json, TRUE);

function insert_schedule_record($dbh, $obj) : int {
    $status = 1 << 13;
    if (is_numeric("" . $obj["id"])) {
        $id = intval($obj["id"]);
        $status |= 1 << 14;
        // check that id exists in schedule then select record with next higher date_time
        $q = "SELECT `date_time` FROM `schedule` WHERE `date_time` >= (SELECT `date_time` FROM `schedule` WHERE `id` = " . $id . ") ORDER BY `date_time` LIMIT 2";
        if ($res = mysqli_query($dbh, $q)) {
            $dates = [];
            while ($row = mysqli_fetch_assoc($res)) {
                $status |= 1 << 15;
                $dates[] = strtotime($row['date_time']);
            }
            if (count($dates) == 2) {
                $new_date_time = date("Y-m-d H:i:s", intval(($dates[0] + $dates[1]) * 0.5));
            } elseif (count($dates) == 1) {
                $new_date_time = date("Y-m-d H:i:s", $dates[0] + (12 + 3600));
            } else {
                $new_date_time = "";
            }
            if ($new_date_time != "") {
                $status |= 1 << 16;
                $q = "INSERT INTO `schedule` (`date_time`) VALUES ('" . $new_date_time . "')";
                if ($res = mysqli_query($dbh, $q)) {
                    $status |= 1 << 17;
                }
            }
        }
    }
    return $status;
}

$r_val = ["status" => 0, "results" => []];

if (isset($obj["passw"])
    && password_verify($obj["passw"], $password_hash)) {
    $update_status = 0;    
    if (isset($obj["id"])) { // set in common.inc
        $update_status = insert_schedule_record($dbh, $obj);
    }
    $r_val = get_schedule($dbh, $obj);
    $r_val["status"] |= $update_status | (1 << 18);
}

echo json_encode($r_val, JSON_NUMERIC_CHECK);
***REMOVED***
