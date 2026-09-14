<?php
/**
 * refresh-reviews.php — monthly job that keeps the site's Google reviews current.
 *
 * It asks the Google Places API for the business's star rating, total review
 * count and its latest reviews, and merges them into assets/data/reviews.json.
 * The pages read that file (site.js), so the count and the quotes update
 * without editing any HTML. Setup steps: deploy/google-reviews-setup.md.
 *
 * Ways to run it:
 *   cron job (recommended):  php /home/.../public_html/refresh-reviews.php
 *   browser (owner only):    https://reaganleonardmusic.com/refresh-reviews.php?token=SECRET
 *
 * It needs a config file named reviews-config.json, looked for first one level
 * ABOVE public_html (best: not reachable from the web), then next to this file:
 *   { "key": "GOOGLE_API_KEY", "token": "a-long-random-secret" }
 * The Google API key never leaves the server.
 *
 * Google returns at most 5 reviews per request (its "most relevant" ones), so a
 * brand-new review may take a while to appear here. The rating and the total
 * count are always current. tools/scrape-google-reviews.py (run on a PC) can
 * fetch every review when needed.
 */
declare(strict_types=1);

const PLACES_ENDPOINT = 'https://places.googleapis.com/v1/places/';
const DATA_FILE = __DIR__ . '/assets/data/reviews.json';
const CONFIG_FILES = [__DIR__ . '/../reviews-config.json', __DIR__ . '/reviews-config.json'];

header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-store');

function fail(string $msg, int $http = 500): void
{
    if (PHP_SAPI !== 'cli') {
        http_response_code($http);
    }
    echo "ERROR: $msg\n";
    exit(1);
}

/* ---- config and access ------------------------------------------------ */
$config = [];
foreach (CONFIG_FILES as $file) {
    if (is_file($file)) {
        $config = json_decode((string) file_get_contents($file), true);
        if (!is_array($config)) {
            fail("$file is not valid JSON");
        }
        break;
    }
}
if (getenv('GOOGLE_PLACES_KEY') !== false && getenv('GOOGLE_PLACES_KEY') !== '') {
    $config['key'] = getenv('GOOGLE_PLACES_KEY');
}
if (empty($config['key'])) {
    fail('no Google API key. Create reviews-config.json (see deploy/google-reviews-setup.md).', 503);
}
if (PHP_SAPI !== 'cli') {
    $given = (string) ($_GET['token'] ?? '');
    if (empty($config['token']) || $given === '' || !hash_equals((string) $config['token'], $given)) {
        fail('missing or wrong token', 403);
    }
}

/* ---- current data ------------------------------------------------------ */
if (!is_file(DATA_FILE)) {
    fail(DATA_FILE . ' is missing');
}
$data = json_decode((string) file_get_contents(DATA_FILE), true);
if (!is_array($data) || !isset($data['reviews']) || !is_array($data['reviews'])) {
    fail(DATA_FILE . ' is not valid');
}
$placeId = (string) ($config['placeId'] ?? ($data['google']['placeId'] ?? ''));
if ($placeId === '') {
    fail('no placeId in reviews.json or the config');
}

/* ---- ask Google -------------------------------------------------------- */
$url = ($config['endpoint'] ?? PLACES_ENDPOINT) . rawurlencode($placeId) . '?languageCode=en';
$headers = [
    'X-Goog-Api-Key: ' . $config['key'],
    'X-Goog-FieldMask: rating,userRatingCount,reviews,googleMapsUri',
    'Accept: application/json',
];
$status = 0;
$body = '';
if (function_exists('curl_init')) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_FOLLOWLOCATION => false,
    ]);
    $body = (string) curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    if ($err !== '') {
        fail("request failed: $err");
    }
} else {
    $ctx = stream_context_create(['http' => ['header' => implode("\r\n", $headers), 'timeout' => 30, 'ignore_errors' => true]]);
    $body = (string) @file_get_contents($url, false, $ctx);
    foreach ($http_response_header ?? [] as $h) {
        if (preg_match('#^HTTP/\S+\s+(\d+)#', $h, $m)) {
            $status = (int) $m[1];
        }
    }
}
$reply = json_decode($body, true);
if ($status !== 200 || !is_array($reply)) {
    fail("Google answered HTTP $status: " . substr($body, 0, 400));
}
if (!isset($reply['userRatingCount']) && !isset($reply['rating'])) {
    fail('Google answered without rating or review count: ' . substr($body, 0, 400));
}

/* ---- merge ------------------------------------------------------------- */
$normalise = static fn(string $s): string => (string) preg_replace('/[^a-z0-9]+/', '', strtolower($s));
$keyOf = static fn(string $name, string $text): string => $normalise($name) . '|' . substr($normalise($text), 0, 40);
$slug = static function (string $s): string {
    $s = strtolower(trim((string) preg_replace('/[^A-Za-z0-9]+/', '-', $s), '-'));
    return $s === '' ? 'review' : $s;
};

$index = [];
$ids = [];
foreach ($data['reviews'] as $i => $r) {
    $index[$keyOf((string) ($r['name'] ?? ''), (string) ($r['text'] ?? ''))] = $i;
    $ids[] = (string) ($r['id'] ?? '');
}
$added = [];
$refreshed = 0;
$seen = 0;
foreach ($reply['reviews'] ?? [] as $rv) {
    $seen++;
    $name = trim((string) ($rv['authorAttribution']['displayName'] ?? ''));
    $text = trim((string) ($rv['text']['text'] ?? ($rv['originalText']['text'] ?? '')));
    if ($name === '' || $text === '') {
        continue;                       // rating-only reviews have nothing to quote
    }
    $stars = (int) ($rv['rating'] ?? 0);
    $date = substr((string) ($rv['publishTime'] ?? ''), 0, 10);
    $when = (string) ($rv['relativePublishTimeDescription'] ?? '');
    $link = (string) ($rv['googleMapsUri'] ?? '');
    $k = $keyOf($name, $text);
    if (isset($index[$k])) {
        $r = &$data['reviews'][$index[$k]];
        if ($date !== '') { $r['date'] = $date; }
        if ($when !== '') { $r['when'] = $when; }
        if ($link !== '') { $r['url'] = $link; }
        if ($stars > 0) { $r['stars'] = $stars; }
        unset($r);
        $refreshed++;
    } else {
        $id = $base = $slug($name);
        for ($n = 2; in_array($id, $ids, true); $n++) {
            $id = "$base-$n";
        }
        $ids[] = $id;
        $data['reviews'][] = [
            'id' => $id, 'source' => 'Google', 'name' => $name, 'stars' => $stars, 'when' => $when,
            'date' => $date, 'text' => $text, 'role' => '', 'url' => $link !== '' ? $link : (string) ($data['google']['url'] ?? ''),
            'added' => date('Y-m-d'),
        ];
        $index[$k] = count($data['reviews']) - 1;
        $added[] = "$name ($stars stars)";
    }
}
$oldCount = $data['google']['count'] ?? null;
if (isset($reply['rating'])) {
    $data['google']['rating'] = (float) $reply['rating'];
}
if (isset($reply['userRatingCount'])) {
    $data['google']['count'] = (int) $reply['userRatingCount'];
}
if (!empty($reply['googleMapsUri'])) {
    $data['google']['url'] = (string) $reply['googleMapsUri'];
}
$data['google']['fetched'] = date('Y-m-d');
$data['google']['fetchedBy'] = 'refresh-reviews.php';
$data['updated'] = date('Y-m-d');

/* ---- save (write to a temp file first so a crash never leaves a half file) */
$json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
if ($json === false) {
    fail('could not encode the updated data: ' . json_last_error_msg());
}
$tmp = DATA_FILE . '.tmp';
if (file_put_contents($tmp, $json . "\n") === false || !rename($tmp, DATA_FILE)) {
    @unlink($tmp);
    fail('could not write ' . DATA_FILE . ' (check file permissions)');
}

echo "OK " . date('Y-m-d H:i') . "\n";
echo "Google rating: " . ($data['google']['rating'] ?? '?') . "  reviews on Google: " . ($data['google']['count'] ?? '?')
    . ($oldCount !== null && $oldCount !== ($data['google']['count'] ?? null) ? " (was $oldCount)" : '') . "\n";
echo "Reviews returned by Google: $seen  already known: $refreshed  new: " . count($added) . "\n";
foreach ($added as $a) {
    echo "  + $a\n";
}
if ($added) {
    echo "New reviews are stored but not shown until you add their id to \"featured\" in assets/data/reviews.json.\n";
}
echo "Stored reviews: " . count($data['reviews']) . "\n";
