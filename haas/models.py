from django.db import models
from django.conf import settings

class Environment(models.Model):
    """
    Define a DB Environment model

    This model defines a table that will store a list of all known server
    environments. Things like dev, QA, UAT, production, etc.
    """

    environment_id = models.AutoField(primary_key=True)
    env_name = models.CharField('Environment Name',
        help_text='Example: dev, stage, prod.',
        max_length=40)
    env_descr = models.TextField('Long Description', max_length=2000,
        help_text='Enter a longer description including use cases or ' +
            'important notes.'
        )
    created_dt = models.DateField(editable=False)
    modified_dt = models.DateField(editable=False)

    class Meta:
        verbose_name = 'System Environment'
        db_table = 'ele_environment'
        ordering = ['env_name',]

    def __unicode__(self):
        return self.env_name


class Herd(models.Model):
    """
    Define a Postgres Database Herd

    A database herd is basically a postgres cluster. In our case, it's allowed
    to "stampede" anywhere, so the herd itself has some basic attributes that
    should be shared on any server that hosts it. This model defines those
    shared attributes.
    """

    herd_id = models.AutoField(primary_key=True)
    environment = models.ForeignKey('Environment',
        on_delete = models.SET_NULL,
        null=True
    )
    herd_name = models.CharField('Herd Name',
        max_length=40,
        help_text='Used to identify this herd, and for CLI tools like' +
            ' pg_ctlcluster.'
    )
    herd_descr = models.TextField('Long Description',
        max_length=2000,
        help_text='Enter important details, notes, or caveats here.'
    )
    db_port = models.IntegerField('Port',
        default=5432,
        help_text='Connection port for hosting this herd. Used for all hosts.'
    )
    pgdata = models.CharField('Data Root',
        max_length=100,
        help_text='Full path to root data directory. Used for all hosts.'
    )
    vhost = models.CharField('Virtual Host',
        max_length=40,
        help_text='Virtual host name to identify primary herd member.'
    )
    created_dt = models.DateField(editable=False)
    modified_dt = models.DateField(editable=False)

    class Meta:
        verbose_name = 'Herd'
        db_table = 'ele_herd'
        ordering = ['herd_name',]

    def __unicode__(self):
        return self.herd_name + ' - ' + self.environment.env_name


class Server(models.Model):
    """
    Define a Postgres Database Server

    Since we're trying to abstract servers away from the process, this model
    mainly allows the server to exist as a medium. We want to encourage
    distributing a public SSH key to let the tool simply seize control.
    """

    server_id = models.AutoField(primary_key=True)
    environment = models.ForeignKey('Environment',
        on_delete = models.SET_NULL,
        null=True
    )
    hostname = models.CharField('Host Name', max_length=40)
    created_dt = models.DateField(editable=False)
    modified_dt = models.DateField(editable=False)

    class Meta:
        verbose_name = 'Server'
        db_table = 'ele_server'
        ordering = ['hostname',]

    def __unicode__(self):
        return self.hostname + ' - ' + self.environment.env_name


class Instance(models.Model):
    """
    Define a Postgres Database Instance

    Take a herd definition and a server, and an instance is the physical
    manifestation of that relationship. This allows herds to exist on the
    server medium, but the herd is still the main focus.
    """

    instance_id = models.AutoField(primary_key=True)
    herd = models.ForeignKey('Herd', on_delete = models.CASCADE)
    server = models.ForeignKey('Server', on_delete = models.CASCADE)
    version = models.CharField('PG Version',
        editable=False,
        max_length=10,
        blank=True)
    local_pgdata = models.CharField('Data Root Override',
        max_length=100,
        blank=True,
        help_text='Full path to root data directory if different from herd' +
            ' default. May be necessary for legacy systems.'
    )
    xlog_pos = models.CharField('Current XLOG Position',
        editable=False,
        max_length=40
    )
    is_online = models.BooleanField('Online', editable=False, default=False)

    master = models.ForeignKey('self',
        on_delete = models.SET_NULL,
        null=True,
        blank=True,
        help_text='If this is a replica, the upstream data source.'
    )

    created_dt = models.DateField(editable=False)
    modified_dt = models.DateField(editable=False)

    class Meta:
        verbose_name = 'Instance'
        db_table = 'ele_instance'
        ordering = ['herd']

    def __unicode__(self):
        return self.herd.herd_name + ' - ' + self.herd.environment.env_name
