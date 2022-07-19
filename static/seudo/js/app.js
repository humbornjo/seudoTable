let handsontable;

$(function () {
    // fix adminLTE incompatibility between fixed layout and !expandOnHover sidebar
    // remove fixed from HTML
    // set height to content-wrapper
    // sidebar overflow is disabled -> use only if you have a short nav in sidebar
    if ($("body").hasClass('sde-fixed')) {
        $("body").removeClass('sde-fixed');
        $(".content-wrapper").css("max-height", `calc(100vh - ${$('.main-header').height()}px`);
        $('body, .wrapper').addClass('overflow-hidden');
        reRenderHandsontable();
        calcControlSidebarHeight();
    }

    // if "multi-step" is in sidebar, add scrollbar
    setTimeout(function () {
        const sideBarMenuHeight = $('.sidebar-menu.tree').height();

        $('.multiStepScrollbar').slimScroll({
            height: `calc(100vh - 100px - ${sideBarMenuHeight}px)`,
            size: '3px',
        });
    }, 500);

    // rerender handsontable when click to open/close sidebar
    $(".sidebar-toggle").click(function () {
        reRenderHandsontable();
    });

    // open/close console
    $('#toggle-console').click(function () {
        $('.sticky-footer').toggleClass('close-console');
        $('.sticky-footer').toggleClass('open-console');
        $('.up-down-arrow').toggleClass('fa-caret-up');
        $('.up-down-arrow').toggleClass('fa-caret-down');
        $(".scrollable-area").slimScroll({
            height: '120px', //scrollable-area height-padding
        });
        reRenderHandsontable();
        calcControlSidebarHeight();
    });

    // open/close horizontal multistep
    $('.multiStep-horizontal .close-multistep').click(function () {
        $('.multiStep-horizontal').toggleClass('closed');

        reRenderHandsontable();
        setTimeout(function () {
            calcControlSidebarHeight();
        }, 300);


    });

    // close sidebar control
    $(".control-sidebar .close").click(function () {
        closeRightSidebar();
    })

    // change white-space on cell hover
    $('#handsontable tr td').on('mouseenter', function () {
        $(this).css('white-space', 'normal');
    });
    $('#handsontable tr td').on('mouseleave', function () {
        $(this).css('white-space', 'nowrap');
    });


    // open/close abstract
    $('.abstract .read-more').click(function () {
        $('.abstract').toggleClass('collapsed');
        if ($('.abstract').hasClass('collapsed')) {
            $('.abstract .read-more').text('Show more');
        } else {
            $('.abstract .read-more').text('Show less');
        }
    });


    $("#HOT").click(function () {
        $("body").addClass("control-sidebar-open");
        calcControlSidebarHeight();
        reRenderHandsontable();
    })

});

$(window).resize(function () {
    reRenderHandsontable();
});

/* ===============
   UTILITIES
   =============== */

//prevent click if btn is disabled
$('.disabled').on('click', function (e) {
    e.preventDefault();
});

/* ===============
   PAGE/SECTION CALC HEIGHT UTILITIES
   =============== */

function calcPageContentHeight() {
    const bodyHeight = '100vh';
    const headerHeight = $('.main-header').height();
    const footerHeight = $('.sticky-footer').outerHeight() !== undefined ? $('.sticky-footer').outerHeight() : 0;
    const multistepHeight = $('.multiStep-horizontal').outerHeight()
    const contentPadding = $('.content').css('padding').replace("px", "") * 2;
    if (!isNaN(multistepHeight))
        return `calc(${bodyHeight} - ${headerHeight}px - ${footerHeight}px - ${contentPadding}px - ${multistepHeight}px)`;

    return `calc(${bodyHeight} - ${headerHeight}px - ${footerHeight}px - ${contentPadding}px)`;
}

function calcControlSidebarHeight() {
    setTimeout(function () {
        let newControlSidebarheigth;
        let newInfoBoxHeight;
        const bodyHeight = '100vh';
        const headerHeight = $('.main-header').height();
        const footerHeight = $('.sticky-footer').outerHeight();
        const multistepHeight = $('.multiStep-horizontal').outerHeight()
        const contentPadding = $('.content').css('padding').replace("px", "") * 2;

        if ($('body').hasClass('inner-control-sidebar')) {
            if (!isNaN(multistepHeight))
                newControlSidebarheigth = newInfoBoxHeight = `calc(${bodyHeight} - ${headerHeight}px - ${footerHeight}px - ${multistepHeight}px)`;
            else
                newControlSidebarheigth = newInfoBoxHeight = `calc(${bodyHeight} - ${headerHeight}px  - ${footerHeight}px`;
        } else {
            newControlSidebarheigth = `calc(${bodyHeight} - ${footerHeight}px`;
            newInfoBoxHeight = `calc(${bodyHeight} - ${headerHeight}px  - ${footerHeight}px`;
        }


        $(".control-sidebar, #infoBox").css('height', newControlSidebarheigth);
        $("#infoBox").slimScroll({
            height: newInfoBoxHeight
        })
    }, 300);

}


/* ===============
   RIGHT SIDEBAR
   =============== */

// open/close sidebar right
function openRightSidebar() {
    if (!$("#sidebar").length) {
        $('body').addClass('control-sidebar-open');
        calcControlSidebarHeight();
        reRenderHandsontable();
    }
}

function closeRightSidebar() {
    $("body").removeClass("control-sidebar-open");
    reRenderHandsontable();

    if ($.find(".handsontable-col-opacity").length) {
        resetHandsontableSettings();
    }

}


/* ===============
   HANDSONTABLE
   =============== */

// update HOT to highlight columns
function updateHandsontableSetting(clickedHoveredCol, subColIndex) {

    if (typeof handsontable !== 'undefined') {
        handsontable.updateSettings({
            cells(row, col) {
                if (col !== clickedHoveredCol && col !== subColIndex) {
                    handsontable.setCellMeta(this.instance.toVisualRow(row), col, 'className', 'opacity-low');
                }
            },
            afterGetColHeader(col, TH) {
                if (col !== clickedHoveredCol && col !== subColIndex) {
                    Handsontable.dom.addClass(TH, 'opacity-low');
                } else {
                    Handsontable.dom.removeClass(TH, 'opacity-low');
                }
            },
        });
    }
}

// reset Handsontable Settings
function resetHandsontableSettings() {
    if (typeof handsontable !== 'undefined') {
        handsontable.updateSettings({
            cells(row, col) {
                handsontable.setCellMeta(row, col, 'className', '');
            },
            afterGetColHeader(col, TH) {
                Handsontable.dom.removeClass(TH, 'opacity-low');
            },
        });
    }
}


function reRenderHandsontable() {
    $('.content-wrapper').css('overflow', 'hidden');
    setTimeout(function () {
        const newWidthTable =
            $('body').filter('.inner-control-sidebar.control-sidebar-open').length > 0
                ? $('.content').width() //- $('.control-sidebar').width()
                : $('.content').width();

        if (handsontable) {
            handsontable.updateSettings({
                height: calcPageContentHeight(),
                width: newWidthTable,
            });
        }
        setTimeout(function () {
            $('.content-wrapper').css('overflow', 'auto');
        }, 2000);
    }, 300);
}


/* ===============
   STYLE UTILITIES
   =============== */

// remove schema from url; if url is undefined, return an alternative string
function removeUrlSchema(url, alternativeString) {
    if (url !== undefined && url !== '') {
        if (url.indexOf('XMLSchema#') > -1) {
            return `xsd:${url.toString().split('#').pop()}`;
        }
        return url.toString().split('/').pop();
    }
    return alternativeString;
}

function animateSendButton(button) {
    // animate send button
    $(button).addClass('click');
    $(button).find('span').text('Saved');
}

// adjust prefix space
function prefixSpace() {

    setTimeout(function () {
        const prefixDbo = $('.showRow .material.prefix-dbo');
        $(prefixDbo).find('input').css('padding-left', `${$(prefixDbo).find('.prefix').outerWidth() + 3}px`);
    }, 50);
}

// reset "save" button to initial state
function resetSaveButton() {
    const submitBtn = $('.submit-form');
    if (submitBtn.hasClass('click')) {
        submitBtn.removeClass('click');
        submitBtn.find('span').text('Save');
    }
}

//unpack

