<?php

/**
 * Demonstrates usage of Oneline Stream
 * support. Input will be in type JSON
 * available as the second argument
 */

$input = json_decode($argv[1]);


file_put_contents("./stream_results", var_dump($input));
?>
