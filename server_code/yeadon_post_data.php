***REMOVED***
header("Content-Type: application/json; charset=UTF-8");
header("Accept: application/json");

require_once 'common.inc';

$rawData = file_get_contents("php://input");
$obj = json_decode($rawData, true);
//echo "Test page<br/>";
$status = 0;
if ($obj === null && json_last_error() !== JSON_ERROR_NONE) {
    $error = json_last_error_msg();
    // Handle the error (e.g., log it or send an error response)
    echo "error = " . $error . "<br/>"; // send back diagnostic code
} else {
    $status = 1;
    $locations = $obj['locations'] ?? null;
    if ($locations) {
        $status = 2;
        $uid = $obj['uid'] ?? null;
        $race = $obj['race'] ?? null;
        foreach ($locations as $value) {
            $time = $value[0];
            $lat = $value[1];
            $lon = $value[2];
            $q = "INSERT INTO `race_locations` (`race`, `time`, `uid`, `lat`, `lon`) VALUES ('". $race . "', " . $time . ", '" . $uid . "', " . $lat . ", " . $lon .")";
            if ($res = mysqli_query($dbh, $q)) {
                $status = 3;
            }
        }
    }
}
echo $status;