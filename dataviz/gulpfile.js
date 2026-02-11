var yargs = require('yargs');
var argv = yargs.argv;

var through2 = require('through2');
var request = require('request');

try {
    var config = require('./config.js');
} catch (ex) {
    if (ex.code === 'MODULE_NOT_FOUND') {
        console.error('\x1b[31m', '!!! config.js doest not exists ! Before starting, copy config.example.js to config.js and fill in your parameters\n' +
            'To do so, copy/paste the following command : \n\t\t cp config.example.js config.js')
    } else {
        console.error('\x1b[31m', '!!! config.js error, check the stack to fix it')
        console.error(ex);
    }
    process.exit(1);
}

const HttpsProxyAgent = require("https-proxy-agent");
var httpsAgent = null;
if (config.PROXY_URL) {
    httpsAgent = new HttpsProxyAgent.HttpsProxyAgent(config.PROXY_URL);
}

var gulp = require('gulp');
var git = require('gulp-git');

var del = require('del');
gulp.task('clean', function () {
    return del([config.OUTPUT_DIR, 'tmp']);
});

/* SERVER */
var gls = require('gulp-live-server');
var browserSync = require('browser-sync');
var sass = require('gulp-dart-sass');

var expressapp = function (done) {
    var server = gls.new(['./app.js', '--port', config.SERVER_PORT]);
    server.start();
    done();
};

var browsersync = function (done) {
    browserSync.init({
        proxy: "http://localhost:" + config.SERVER_PORT,
        files: config.WATCH_DIRS,
        browser: config.BROWSER,
        port: (1 * config.SERVER_PORT + 1),
    });

    gulp.watch('pages/views/**/*', browserSync.reload);

    gulp.watch(['pages/styles/**/*.scss', 'ods-portal/**/*.scss'], gulp.series('sass-sync'));
};

gulp.task('sass-sync', function () {
    return gulp.src(['kit/styles/index.scss', 'kit/styles/index-pages.scss', 'pages/styles/**/*.scss'])
        .pipe(sass())
        .pipe(gulp.dest('output'))
        .pipe(browserSync.stream());
});

gulp.task('server', gulp.series('sass-sync', expressapp, browsersync));

/* HTML */
var ejs = require('ejs');
const rename = require('gulp-rename');

gulp.task('compile-html', function () {
    var page_list = [];
    config.PAGES.forEach(function (page) {
        page_list.push('pages/views/' + page + '.ejs');
    });
    return gulp.src(page_list)
        .pipe(through2.obj(function (file, enc, cb) {
                ejs.renderFile(file.path, {slug: file.basename.replace('.ejs','')}, {}, (err, str) => {
                    file.contents = Buffer.from(str);
                    cb(null, file);
                })
            })
        )
        .pipe(rename(function (path) {
            path.extname = '.html';
        }))
        .pipe(gulp.dest(config.OUTPUT_DIR));
});

/* CSS */
var path = require('path');

gulp.task('compile-css', function () {
    var page_list = [];
    config.PAGES.forEach(function (page) {
        page_list.push('pages/styles/' + page + '.scss');
    });
    return gulp.src(page_list)
        .pipe(sass())
        .pipe(rename(function (path) {
            path.extname = '.css';
        }))
        .pipe(gulp.dest(config.OUTPUT_DIR));
});

gulp.task('compile', gulp.series('clean', 'compile-html', 'compile-css'));

/* API Managment */
var fs = require('fs');
var axios = require("axios");

gulp.task('get', function (cb) {
    var requests = [];
    config.PAGES.forEach(function (page) {
        requests.push(axios({
            method: 'get',
            url: 'https://' + config.ODS_PORTAL_DOMAIN_ID + config.ODS_PORTAL_SUFFIX + '/api/management/v2/pages/' + page,
            headers: {
                "Authorization": `apikey ${config.ODS_ADMIN_APIKEY}`
            },
            validateStatus: function (status) {
                return status >= 200 && status < 300; // default
            },
            httpsAgent
        }));
    });

    axios.all(requests)
        .catch(function (error) {
            let err = error.toJSON();
            console.error(`${err.name}, ${err.message}\nurl: ${err.config.url}`);
            if (err.message.indexOf('ECONNREFUSED') >= 0 && err.config.url.indexOf('<DOMAIN ID>') < 0) {
                console.error('Erreur de connexion et de requête Web, merci de vérifier votre connexion internet et/ou proxy pour accéder au portail ODS');
            }
            if (err.config.url.indexOf('<DOMAIN ID>') >= 0)
                console.error('Did you replace <DOMAIN ID> by your domain id in your config.project.js file ?');
            throw error;
        })
        .then(function (responses) {
            responses.forEach(function (response) {
                fs.mkdir(path.join(__dirname, config.OUTPUT_DIR), {recursive: true}, (err) => {
                    if (err) throw err;
                });
                fs.writeFileSync(path.join(__dirname, config.OUTPUT_DIR, response.data.slug + '.json'), JSON.stringify(response.data));
            });
            cb();
        });
});

var jeditor = require("gulp-json-editor");

gulp.task('edit', function () {
    return gulp.src(path.join(__dirname, config.OUTPUT_DIR, '*.json'))
        .pipe(jeditor(function (json) {
            var slug = json.slug;
            json.slug = undefined;
            json.pushed_by_parent = undefined;
            json.has_subdomain_copies = undefined;
            json.created_at = undefined;
            json.last_modified = undefined;
            json.last_modified_user = undefined;
            json.author = undefined;
            Object.keys(json.content.html).forEach(function (key) {
                json.content.html[key] = fs.readFileSync(path.join(__dirname, config.OUTPUT_DIR, slug + '.html'), "utf8");
                json.content.css[key] = fs.readFileSync(path.join(__dirname, config.OUTPUT_DIR, slug + '.css'), "utf8");
            });
            return json;
        }))
        .pipe(gulp.dest(path.join(__dirname, config.OUTPUT_DIR)));
});

gulp.task('put', function () {
    return gulp.src(path.join(__dirname, config.OUTPUT_DIR, '*.json'))
        .pipe(through2.obj(function (file, enc, cb) {
                request.put({
                    url: 'https://' + config.ODS_PORTAL_DOMAIN_ID + config.ODS_PORTAL_SUFFIX + '/api/management/v2/pages/' + file.basename.replace('.json', ''),
                    json: JSON.parse(file.contents.toString()),
                    headers: {
                        "Authorization": `apikey ${config.ODS_ADMIN_APIKEY}`,
                        'Content-Type': 'application/json'
                    },
                    agent: httpsAgent
                }, function (error, response, body) {
                    if (error) {
                        console.log(error);
                    } else if (response) {
                        if (response.body.errors && response.body.errors.length > 0 && response.body.errors[0].status_code >= 400) {
                            console.error("ERROR Received from API for page ID \"" + file.basename.replace('.json', '') + "\"");
                            console.error(response.body.errors[0].message);
                            console.debug(JSON.stringify(response.body));
                        } else {
                            console.log('API Page update successful on "' + response.body.slug + '"');
                            cb();
                        }
                    }
                })
            }
        ));
});

gulp.task('update', gulp.series('compile', 'get', 'edit', 'put'));

/* Versioning */

/*
git checkout master
git branch xxx
git checkout xxx
git commit -m "init"
git push --set-upstream origin xxx
 */
gulp.task('newproject', async function (done) {
    if (!argv.name) {
        console.error('\x1b[31m', 'A project name must be provided, for example : \n\t gulp newproject --name <project name>');
        return;
    }
    git.checkout("master", function (err) {
        if (err) {
            throw err;
        } else {
            git.branch(argv.name, function (err) {
                if (err) {
                    if (err.code == 128) {
                        console.error('\x1b[31m', "Project '" + argv.name + "' already exists, load it or choose another name");
                        return;
                    }
                } else {
                    git.checkout(argv.name, function (err) {
                        if (err) {
                            throw err;
                        } else {
                            git.commit('initial commit', {args: '-a'}, function (err) {
                                if (err) {
                                    throw err;
                                } else {
                                    git.push('origin', argv.name, {args: '--set-upstream'}, function (err) {
                                        if (err) {
                                            throw err;
                                        } else {
                                            console.log('Project created !');
                                            done();
                                        }
                                    });
                                }
                            })
                        }
                    });
                }
            });
        }
    });
});

gulp.task('loadproject', async function (done) {
    if (!argv.name) {
        console.error('\x1b[31m', 'A project name must be provided, for example : \n\t gulp loadproject --name <project name>');
        return;
    }
    git.checkout(argv.name, function (err) {
        if (err) {
            if (err.code == 128) {
                console.error('\x1b[31m', "Project '" + argv.name + "' does not exists");
                return;
            } else {
                throw err;
            }
        }
        done();
    });
});

var log = require('fancy-log');
var exec = require('child_process').exec;

gulp.task('listprojects', function (done) {
    var cwd = process.cwd();
    var args = '--list';
    var cmd = 'git show-branch ' + args;
    return exec(cmd, {cwd: cwd}, function (err, stdout, stderr) {
        if (err) return cb(err);
        log(stdout, stderr);
    });
});

gulp.task('listremoteprojects', function (done) {
    var cwd = process.cwd();
    var args = '--list -r';
    var cmd = 'git show-branch ' + args;
    return exec(cmd, {cwd: cwd}, function (err, stdout, stderr) {
        if (err) return cb(err);
        log(stdout, stderr);
        log('\x1b[32m', 'The format is :\n  [origin/<project name>] <last comment>');
    });
});

/*
$ git push -d <remote_name> <branch_name>
$ git branch -d <branch_name>
 */
gulp.task('deleteproject', function (done) {
    if (!argv.name) {
        console.error('\x1b[31m', 'A project name must be provided, for example : \n\t gulp deleteproject --name <project name>');
        return;
    }
    git.branch(argv.name, {args: "-D"}, function (err) {
        if (err) {
            if (err.code == 1) {
                console.error('\x1b[31m', "Project '" + argv.name + "' does not exists locally !");
                return;
            } else {
                throw err;
            }
        } else {
            console.log('\x1b[32m', 'Project locally deleted successfully');
            git.push("origin", argv.name, {args: "-d"}, function (err) {
                if (err) {
                    console.log(err.code);
                    if (err.code == 1) {
                        console.error('\x1b[31m', "Project '" + argv.name + "' does not exists remotely !");
                        return;
                    } else {
                        throw err;
                    }
                }
                console.log('\x1b[32m', 'Project remotely deleted successfully');
                done();
            });
        }
    })
});

var commit = function () {
    return gulp.src('.').pipe(git.add()).pipe(git.commit(argv.comment, {args: ''}, function (err) {
        if (err) throw err;
    }));
};

var push = function (done) {
    git.push('origin', function (err) {
        if (err) {
            throw err;
        } else {
            console.log('\x1b[32m', 'Project saved');
            done();
        }
    });
};

var merge = function (done) {
    git.checkoutFiles('', {args: '--theirs master app.js compile.js gulpfile.js config.example.js package.json static/ods-internal/* static/ods-widgets/*'}, function (err) {
        if (err) {
            throw err;
        }
    });
    argv.comment = "Upgrade kit by merging master into the current project";
    done();
}

/*
git commit -a -m "MSG"
git push
 */
gulp.task('save', async function (done) {
    if (!argv.comment || argv.comment === true) {
        console.error('\x1b[31m', 'Your save must contain a comment between quotes,\n\t gulp save --comment "ici ou là bas"');
        return;
    }
    gulp.series(commit, push)();
});

/*
    Checkout kit files, and commit and push
 */
gulp.task('upgrade', async function (done) {
    gulp.series(merge, commit, push)();
});


gulp.task('default', function (done) {
    console.log("\n-- Welcome to Opendatasoft local development kit --\n");
    console.log("\t Main commands are :\n");
    console.log("\t> gulp server (to run the local server and run your work");
    console.log("\t> gulp update (to upload your work on your Opendatasoft portal, don't forget to add your settings in config.js");
    console.log("\n\t For users working in a git repository, some command to keep tracks of your changes :");
    console.log("\t> gulp newproject (create a new project, ie create a branch)");
    console.log("\t> gulp loadproject (load a project locally, or download and load a remote project if it's remote, ie checkout an existing branch)");
    console.log("\t> gulp listprojects (list all > gulp save (to save keep tracks of your changes)");
    console.log("\t> gulp listremoteprojects (list all existing project, locally and remotely)");
    console.log("\t> gulp deleteproject (delete a project locally and remotely ! beware !)");
    console.log("\t> gulp save (save your work and push it remotely for backup, ie commit and push your code)");
    console.log("\t> gulp upgrade (to get the last version of the kit into your current project, ie checkout and merge the kit files from master branch)");
    console.log("\t> gulp --tasks (to see all available tasks)");
    console.log("\n");
    done();
});