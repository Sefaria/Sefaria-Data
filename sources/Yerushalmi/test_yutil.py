# -*- coding: utf-8 -*-
import django
django.setup()
import yutil
import pytest


class TestOverlay(object):
    def test_two_tags(self):
        ma = yutil.MishnahAlignment("Eruvin", 1, 1, yutil.venice, yutil.gugg, "./v_comp", skip_mishnah=True)
        ma.import_xlsx()
        r = ma.get_b_with_a_marks("bob")
        assert r[0].startswith('<i data-overlay="bob" data-value="18b"></i>')
        marker_18c = "עוֹשֶׂה חָרִיץ עַל" + " " + '<i data-overlay="bob" data-value="18c"></i>' + "פֶּתַח הַמָּבוֹי עָמוֹק עֲשָׂרָה"
        assert marker_18c in r[4]
        marker_18d = "רִבִּי יִרְמְיָה אָמַר." + " " + '<i data-overlay="bob" data-value="18d"></i>' + "רִבִּי זֵירָא"
        assert marker_18d in r[14]

class TestTaggedTextBlock(object):
    no_tag = '  וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי.  '
    one_internal_tag_pair = '    רִבִּי יוּדָן בְּעָא. כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.  '
    with_starting_tag = ' ' + ' <i data-overlay="Venice Pages" data-value="2d"></i> ' + '    רִבִּי יוּדָן בְּעָא. כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.  '
    with_ending_tag = '    רִבִּי יוּדָן בְּעָא. כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.  ' + '<i data-overlay="Venice Pages" data-value="2d"></i>' + ' '

    # <i data-overlay="Venice Pages" data-value="2d"></i>
    def test_identity_simple(self):
        assert yutil.TaggedTextBlock(self.no_tag).as_text() == self.no_tag

    def test_identity_simple_with_space(self):
        assert yutil.TaggedTextBlock(self.no_tag.strip()).as_text() == self.no_tag.strip()

    def test_identity_with_tag(self):
        assert yutil.TaggedTextBlock(self.one_internal_tag_pair).as_text() == self.one_internal_tag_pair

    def test_identity_with_tag_with_space(self):
        assert yutil.TaggedTextBlock(self.one_internal_tag_pair.strip()).as_text() == self.one_internal_tag_pair.strip()

    def test_identity_with_ending_tag(self):
        assert yutil.TaggedTextBlock(self.with_ending_tag.strip()).as_text() == self.with_ending_tag.strip()

    def test_identity_with_starting_tag(self):
        assert yutil.TaggedTextBlock(self.with_starting_tag.strip()).as_text() == self.with_starting_tag.strip()

    def test_identity_with_starting_tag_and_space(self):
        assert yutil.TaggedTextBlock(self.with_starting_tag).as_text() == self.with_starting_tag

    def test_identity_with_ending_tag_and_space(self):
        assert yutil.TaggedTextBlock(self.with_ending_tag).as_text() == self.with_ending_tag

    def test_insert_tag(self):
        expected_result = '    רִבִּי יוּדָן בְּעָא. <i data-layer="roger"></i>כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.  '
        first_tt = yutil.TaggedTextBlock(self.one_internal_tag_pair)
        first_tt.insert_tag_after_word(3, "i", {"data-layer": "roger"})
        assert first_tt.as_text() == expected_result

    def test_insert_tag_at_beginning(self):
        expected_result = '     <i data-layer="roger"></i>רִבִּי יוּדָן בְּעָא. כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.  '
        first_tt = yutil.TaggedTextBlock(self.one_internal_tag_pair)
        first_tt.insert_tag_after_word(0, "i", {"data-layer": "roger"})
        assert first_tt.as_text() == expected_result

