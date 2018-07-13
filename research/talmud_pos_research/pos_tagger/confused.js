/**
 * Created by nss on 10/21/16.
 */
console.log("hello");

$(function() {
    $('body')
        .append('<div data-yo="guessed" style="position: absolute;text-align: center;background:orange;border: solid 1px black;padding:10px"></div>')
        .append('<div data-yo="correct" style="position: absolute;text-align: center;background:orange;border: solid 1px black;padding:10px"></div>');


   $("[data-i]").hover(
       function() {
           var row = $(this).data('i');
           var col = $(this).data('j');
           var col_pos = $('[data-col-head="'+col+'"]').html();
           var row_pos = $('[data-row-head="'+row+'"]').html();
           var x = $(this).position().left;
           var y = $(this).position().top;
           var w = $(this).width();
           var h = $(this).height();

           $('[data-yo="guessed"]').css({'width':30,'height':h,'top':y,'left':x-h-40}).html(row_pos);
           $('[data-yo="correct"]').css({'width':w,'height':30,'top':y-w-20,'left':x}).html(col_pos);


           console.log("Correct",col_pos,"Guessed",row_pos,$(this).position(),$(this).width(),$(this).height());


   }, function() {
        console.log("out");
   });
});