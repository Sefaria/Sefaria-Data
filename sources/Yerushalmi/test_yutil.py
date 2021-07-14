# -*- coding: utf-8 -*-
import django
django.setup()
import yutil
import pytest


class TestTaggedTextBlock:
    no_tag = '  וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי.  '
    one_internal_tag_pair = '    רִבִּי יוּדָן בְּעָא. כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.  '
    with_starting_tag = ' ' + ' <i data-overlay="Venice Pages" data-value="2d"></i> ' + '    רִבִּי יוּדָן בְּעָא. כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.  '
    with_ending_tag = '    רִבִּי יוּדָן בְּעָא. כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.  ' + '<i data-overlay="Venice Pages" data-value="2d"></i>' + ' '

    # <i data-overlay="Venice Pages" data-value="2d"></i>
    def test_identity_simple(self):
        assert yutil.TaggedTextBlock(self.no_tag).as_text() == self.no_tag
        assert yutil.TaggedTextBlock(self.no_tag.strip()).as_text() == self.no_tag.strip()

    def test_identity_with_tag(self):
        assert yutil.TaggedTextBlock(self.one_internal_tag_pair).as_text() == self.one_internal_tag_pair
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
        first_tt = yutil.TaggedTextBlock(self.one_internal_tag_pair)
        first_tt.insert_tag_after_word(3,"i",{"data-layer":"roger"})
        second_tt = yutil.TaggedTextBlock(first_tt.as_text())
        assert second_tt._parts[0]["word_count"] == 3
