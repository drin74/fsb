package com.fsb.registry.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.recyclerview.widget.RecyclerView
import com.fsb.registry.data.Client
import com.fsb.registry.R

class ClientAdapter(
    private val onClick: (Client) -> Unit,
) : RecyclerView.Adapter<ClientAdapter.VH>() {

    private val items = mutableListOf<Client>()

    inner class VH(view: View) : RecyclerView.ViewHolder(view) {
        val card: CardView = view.findViewById(R.id.itemRoot)
        val tvName: TextView = view.findViewById(R.id.tvItemName)
        val tvPhone: TextView = view.findViewById(R.id.tvItemPhone)
        val tvStatus: TextView = view.findViewById(R.id.tvItemStatus)
        val tvRisk: TextView = view.findViewById(R.id.tvItemRisk)
        val tvSource: TextView = view.findViewById(R.id.tvItemSource)
        val tvUpdated: TextView = view.findViewById(R.id.tvItemUpdated)

        fun bind(client: Client) {
            tvName.text = client.fullName ?: "${client.lastName ?: ""} ${client.firstName ?: ""}".trim()
            tvPhone.text = client.phone ?: "контакты не указаны"
            tvStatus.text = client.status?.replace('_', ' ')?.replaceFirstChar { it.uppercaseChar() } ?: ""
            tvRisk.text = client.riskLevel?.replace('_', ' ')?.replaceFirstChar { it.uppercaseChar() } ?: ""
            tvSource.text = client.sourceName ?: "Ручной ввод"
            tvUpdated.text = client.updatedAt ?: ""
            itemView.setOnClickListener { onClick(client) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_client, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount(): Int = items.size

    fun submit(list: List<Client>) {
        items.clear()
        items.addAll(list)
        notifyDataSetChanged()
    }
}
