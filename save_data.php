<?php
$servername = "localhost";
$username = "ESP8266NPL";
$password = "VCI_ioCJa1M574_p";
$dbname = "arduino_data";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Check if data is received
if (isset($_POST['X1']) && isset($_POST['X2']) && isset($_POST['Y1']) && isset($_POST['Y2']) &&
    isset($_POST['D1']) && isset($_POST['D2']) && isset($_POST['Z1']) && isset($_POST['Z2'])) {

    $X1 = $_POST['X1'];
    $X2 = $_POST['X2'];
    $Y1 = $_POST['Y1'];
    $Y2 = $_POST['Y2'];
    $D1 = $_POST['D1'];
    $D2 = $_POST['D2'];
    $Z1 = $_POST['Z1'];
    $Z2 = $_POST['Z2'];

    // Insert data into database
    $sql = $conn->prepare("INSERT INTO sensordata (X1, X2, Y1, Y2, D1, D2, Z1, Z2) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
    $sql->bind_param('dddddddd', $X1, $X2, $Y1, $Y2, $D1, $D2, $Z1, $Z2);

    if ($sql->execute()) {
        echo "New record created successfully";
    } else {
        echo "Error: " . $sql->error;
    }

    $sql->close();
} else {
    echo "No data received";
}

$conn->close();
?>
