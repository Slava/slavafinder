#include <gtk/gtk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DESCRIPTION "Drag and Drop Between 2 Treeviews - by Vikram Ambrose"

/* Row data structure */
struct DATA {
        char *row;
        char *item;
        int qty;
        float price;
};

/* A convenience enumerator to tag data types */
enum {
        TARGET_STRING,
        TARGET_INTEGER,
        TARGET_FLOAT
};

/* A convenience enumerator to count the columns */
enum {
        ROW_COL=0,
        ITEM_COL,
        QTY_COL,
        PRICE_COL,
        NUM_COLS
};

/* Some sample data for treeview 1. A NULL row is added so we dont
   need to pass around the size of the array */
static struct DATA row_data[] = {
        { "row0","item 12", 3, 4.3 },
        { "row1","item 23", 44,34.4},
        { "row2","item 33", 34,25.4},
        { "row3","item 43", 37,64.4},
        { "row4","item 53", 12,14.4},
        { "row5","item 68", 42,34.4},
        { "row6","item 75", 72,74.4},
        {NULL}
};

/* Sample data for treeview 2 */
static struct DATA row2_data[] = {
        {"row7", "item 127", 105, 115.5},
        {"row8","item 124", 117, 118.6},
        {"row9", "item 123", 120, 121.73},
        {NULL}
};

static const GtkTargetEntry drag_targets = {
        "STRING", GTK_TARGET_SAME_APP,TARGET_STRING
};

static guint n_targets = 1;

/* Could be used instead, if GtkTargetEntry had more than one row */
//static guint n_targets = G_N_ELEMENTS (drag_targets);

/* Convenience function to deallocated memory used for DATA struct */
void free_DATA(struct DATA *data){
        if(data){
                free(data->row);
                free(data->item);
        }
        free(data);
}

/* Convenience function to print out the contents of a DATA struct onto stdout */
void print_DATA(struct DATA *data){
        printf("DATA @ %p\n",data);
        printf(" |->row = %s\n",data->row);
        printf(" |->item = %s\n",data->item);
        printf(" |->qty = %i\n",data->qty);
        printf(" +->price = %f\n",data->price);
}

/* User callback for "get"ing the data out of the row that was DnD'd */
void on_drag_data_get(  GtkWidget *widget, GdkDragContext *drag_context,
                        GtkSelectionData *sdata, guint info, guint time,
                        gpointer user_data){
        GtkTreeIter iter;
        GtkTreeModel *list_store;
        GtkTreeSelection *selector;
        gboolean rv;
        printf("on_drag_data_get: ");

        /* Get the selector widget from the treeview in question */
        selector = gtk_tree_view_get_selection(GTK_TREE_VIEW(widget));

        /* Get the tree model (list_store) and initialise the iterator */
        rv = gtk_tree_selection_get_selected(selector,&list_store,&iter);

        /* This shouldn't really happen, but just in case */
        if(rv==FALSE){
                printf(" No row selected\n");
                return;
        }

        /* Always initialise a GValue with 0 */
        GValue value={0,};
        char *cptr;

        /* Allocate a new row to send off to the other side */
        struct DATA *temp = malloc(sizeof(struct DATA));

        /* Go through the columns */

        /* Get the GValue of a particular column from the row, the iterator currently points to*/
        gtk_tree_model_get_value(list_store,&iter,ROW_COL,&value);
        cptr = (char*) g_value_get_string(&value);
        temp->row = malloc(strlen(cptr)*sizeof(char)+1);
        strcpy(temp->row,cptr);
        g_value_unset(&value);

        gtk_tree_model_get_value(list_store,&iter,ITEM_COL,&value);
        cptr = (char*)g_value_get_string(&value);
        temp->item = malloc(strlen(cptr)*sizeof(char)+1);
        strcpy(temp->item,cptr);
        g_value_unset(&value);

        gtk_tree_model_get_value(list_store,&iter,QTY_COL,&value);
        temp->qty = g_value_get_int(&value);
        g_value_unset(&value);

        gtk_tree_model_get_value(list_store,&iter,PRICE_COL,&value);
        temp->price = g_value_get_float(&value);
        g_value_unset(&value);

        /* Send the data off into the GtkSelectionData object */
        gtk_selection_data_set(sdata,
                gdk_atom_intern ("struct DATA pointer", FALSE),
                8,              /* Tell GTK how to pack the data (bytes) */
                (void *)&temp,  /* The actual pointer that we just made */
                sizeof (temp)); /* The size of the pointer */

        /* Just print out what we sent for debugging purposes */
        print_DATA(temp);
}

/* User callback for putting the data into the other treeview */
void on_drag_data_received(GtkWidget *widget, GdkDragContext *drag_context,
                        gint x, gint y, GtkSelectionData *sdata, guint info,
                        guint time, gpointer user_data){

        GtkTreeModel *list_store;
        GtkTreeIter iter;

        printf("on_drag_data_received:\n");

        /* Remove row from the source treeview */
        GtkTreeSelection *selector;
        selector = gtk_tree_view_get_selection(GTK_TREE_VIEW(user_data));
        gtk_tree_selection_get_selected(selector,&list_store,&iter);
        gtk_list_store_remove(GTK_LIST_STORE(list_store),&iter);

        /* Now add to the other treeview */
        GtkTreeModel *list_store2;
        GtkTreeIter iter2;
        list_store2 = gtk_tree_view_get_model(GTK_TREE_VIEW(widget));
        gtk_list_store_append(GTK_LIST_STORE(list_store2),&iter2);

        /* Copy the pointer we received into a new struct */
        struct DATA *temp = NULL;
        memcpy (&temp, sdata->data, sizeof (temp));

        /* Add the received data to the treeview model */
        gtk_list_store_set(GTK_LIST_STORE(list_store2),&iter2,
                ROW_COL,temp->row,
                ITEM_COL,temp->item,
                QTY_COL,temp->qty,
                PRICE_COL,temp->price,-1);

        /* We dont need this anymore */
        free_DATA(temp);
}

/* User callback just to see which row was selected, doesnt affect DnD.
   However it might be important to note that this signal and drag-data-received may occur at the same time. If you drag a row out of one view, your selection changes too */
void on_selection_changed (GtkTreeSelection *treeselection,gpointer user_data){
        GtkTreeIter iter;
        GtkTreeModel *list_store;
        gboolean rv;
        printf("on_selection_changed: ");

        rv = gtk_tree_selection_get_selected(treeselection,
                &list_store,&iter);
        /* "changed" signal sometimes fires blanks, so make sure we actually
         have a selection/
http://library.gnome.org/devel/gtk/stable/GtkTreeSelection.html#GtkTreeSelection-changed */
        if (rv==FALSE){
                printf("No row selected\n");
                return;
        }

        GValue value={0,};
        char *cptr;
        int i;

        /* Walk throw the columns to see the row data */
        for(i=0;i<NUM_COLS;i++){
                gtk_tree_model_get_value(list_store,&iter,i,&value);
                cptr = (gchar *) g_strdup_value_contents (&value);
                g_value_unset(&value);
                if(cptr)printf("%s|",cptr);
                free(cptr);
        }
        printf("\n");

}

/* Creates a scroll windows,  puts a treeview in it and populates it */
GtkWidget *add_treeview(GtkWidget *box, struct DATA array[]){
        GtkWidget *swindow;

        swindow = gtk_scrolled_window_new(NULL,NULL);

        /* Both Vertical and Horizontal scroll set to Auto (NULL) */
        gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(swindow),
                 GTK_POLICY_AUTOMATIC,GTK_POLICY_AUTOMATIC);

        /* Add this window to the box */
        gtk_box_pack_start(GTK_BOX(box),swindow,TRUE,TRUE,2);

        /* Create the treeview and its list store */
        GtkListStore *list_store;
        list_store = gtk_list_store_new(NUM_COLS,
                G_TYPE_STRING,G_TYPE_STRING,G_TYPE_INT,G_TYPE_FLOAT);

        GtkWidget *tree_view;
        tree_view = gtk_tree_view_new_with_model(GTK_TREE_MODEL(list_store));

        /* Add the treeview to the scrolled window */
        gtk_container_add(GTK_CONTAINER(swindow),tree_view);

        /* Add the columns */
        GtkCellRenderer *renderer;
        GtkTreeViewColumn *column;

        char column_names[NUM_COLS][16] = {
                "Row #", "Description", "Qty", "Price"};
        int i;
        for(i=0;i<4;i++){
                renderer = gtk_cell_renderer_text_new();
                column = gtk_tree_view_column_new_with_attributes (
                        column_names[i],renderer,"text",i,NULL);
                gtk_tree_view_column_set_sort_column_id (column, i);
                gtk_tree_view_append_column (GTK_TREE_VIEW(tree_view), column);
        }

        /* Tell the theme engine we would like differentiated row colour */
        gtk_tree_view_set_rules_hint(GTK_TREE_VIEW(tree_view),TRUE);

        /* Add the data */
        GtkTreeIter iter;
        i=0;
        while(array[++i].row!=NULL){
                gtk_list_store_append(list_store,&iter);
                gtk_list_store_set(list_store,&iter,
                        ROW_COL,array[i].row,
                        ITEM_COL,array[i].item,
                        QTY_COL,array[i].qty,
                        PRICE_COL,array[i].price,-1);
        }

        /* Attach the "changed" callback onto the tree's selector */
        g_signal_connect(
                gtk_tree_view_get_selection (GTK_TREE_VIEW(tree_view)),
                "changed",G_CALLBACK(on_selection_changed),NULL);

        return tree_view;
}

int main(int argc, char **argv){
        GtkWidget *window;

        gtk_init(&argc,&argv);

        /* Create the top level window and setup the quit callback */
        window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
        gtk_window_set_default_size(GTK_WINDOW(window),666,266);
        g_signal_connect(G_OBJECT(window),"destroy",G_CALLBACK(gtk_exit),NULL);

        /* Build up the GUI with some boxes */
        GtkWidget *vbox = gtk_vbox_new(FALSE,10);
        gtk_container_add(GTK_CONTAINER(window),vbox);

        /* Add a title */
        GtkWidget *title = gtk_label_new(DESCRIPTION);
        gtk_box_pack_start(GTK_BOX(vbox),title,FALSE,FALSE,1);

        GtkWidget *hbox = gtk_hbox_new(TRUE,1);
        gtk_box_pack_start(GTK_BOX(vbox),hbox,TRUE,TRUE,1);

        /* Create treeview 1 */
        GtkWidget *view1;
        view1 = add_treeview(hbox,row_data);

        /* Set treeview 1 as the source of the Drag-N-Drop operation */
        gtk_drag_source_set(view1,GDK_BUTTON1_MASK, &drag_targets,n_targets,
                GDK_ACTION_COPY|GDK_ACTION_MOVE);
        /* Attach a "drag-data-get" signal to send out the dragged data */
        g_signal_connect(view1,"drag-data-get",
                G_CALLBACK(on_drag_data_get),NULL);

        /* Create treeview 2 */
        GtkWidget *view2;
        view2 = add_treeview(hbox,row2_data);

        /* Set treeview 2 as the destination of the Drag-N-Drop operation */
        gtk_drag_dest_set(view2,GTK_DEST_DEFAULT_ALL,&drag_targets,n_targets,
                GDK_ACTION_COPY|GDK_ACTION_MOVE);
        /* Attach a "drag-data-received" signal to pull in the dragged data */
        g_signal_connect(view2,"drag-data-received",
                G_CALLBACK(on_drag_data_received),view1);

        /* Rock'n Roll */
        gtk_widget_show_all(window);
        gtk_main();
        return 0;
}
