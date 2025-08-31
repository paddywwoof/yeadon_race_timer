***REMOVED***
header("Content-Type: application/json; charset=UTF-8");
header("Accept: application/json");

require_once 'common.inc';

$rawData = file_get_contents("php://input");
$obj = json_decode($rawData, true);
//echo "Test page<br/>";
$status = 0;
$r_val = ["status" => 0, "results" => []];
if ($obj === null && json_last_error() !== JSON_ERROR_NONE) {
    $error = json_last_error_msg();
    // Handle the error (e.g., log it or send an error response)
    echo "error = " . $error . "<br/>"; // send back diagnostic code
} else {
    $status = 1;
    $race = $obj['race'] ?? null;
    if ($race) {
        // TODO filter SQL injection. race must: 
        if (preg_match('/^[0-9]{6}-[0-9]{4}$/', $race)) {
            $q = "SELECT `time`, `uid`, `lat`, `lon` FROM `race_locations` WHERE `race` = '" . $race . "'";
            $status = 2;
            if ($res = mysqli_query($dbh, $q)) {
                $status = 3;
                while ($row = mysqli_fetch_assoc($res)) {
                    $status = 4;
                    $r_val["results"][] = [$row["uid"], $row["time"], $row["lat"], $row["lon"]];
                }
            }
        } else {
            $status = -2;
        }
    }
}
$r_val["status"] = $status;
echo json_encode($r_val, JSON_NUMERIC_CHECK);
***REMOVED***