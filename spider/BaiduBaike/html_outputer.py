# coding:utf-8
class HtmlOutPuter(object):
    def __init__(self):
        self.datas = []

    def collect_data(self, data):
        if data is None:
            return
        self.datas.append(data)

    def output_html(self):
        with open('output.html', 'w') as fout:
            fout.write('<html>')
            fout.write('<head> <meta charset="UTF-8"> </head>')
            fout.write('<body>')
            fout.write('<table>')
            for data in self.datas:
                fout.write('<tr>')
                fout.write('<td>%s</td>' % data['url'])
                fout.write('<td>%s</td>' % data['title'])
                fout.write('<td>%s</td>' % data['summary'])
                fout.write('</tr>')

            fout.write('</table>')
            fout.write('</body>')
            fout.write('</html>')