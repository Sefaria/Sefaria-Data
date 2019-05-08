import apache_log_parser
import gzip

line_parser = apache_log_parser.make_parser('%a %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"')
num_actual_users = 0
good_user_agents = {'Sefaria', 'Android'}
bad_user_agents = {'Python-urllib', 'UptimeRobot'}
with gzip.open('access.log.2.gz', 'rb') as fin:
    for line in fin:
        parsed = line_parser(line)
        if parsed['status'] == '200' and parsed['request_header_user_agent__browser__family'] in good_user_agents:
            num_actual_users += 1

print num_actual_users


